"""
Fork-specific service layer — business logic for the td-mcp fork tools.

Each method here maps 1:1 to a new MCP tool defined in
``src/features/tools/handlers/forkTools.ts``. The service is intentionally
thin: most of the TD-side heavy lifting lives in ``tdapi`` (the Python
helper library ported from satoruhiga/claude-touchdesigner in Phase 3.1).

Scope:

- :meth:`get_pane` / :meth:`get_selection`        — editor context (#3)
- :meth:`force_cook`                              — recursive cook (#4)
- :meth:`capture_viewport`                        — TOP/COMP/pane capture (#5)
- :meth:`connect_nodes` / :meth:`layout_*`        — wiring + layout (#6)
- :meth:`glsl_read` / :meth:`glsl_write`          — GLSL shader authoring (#7)
- :meth:`scaffold`                                — scene templates (#8)

None of these methods do their own cook-scope recovery — that belongs
higher up the stack (in :mod:`mcp.controllers.fork_controller` which may
wrap mutation calls in an auto-cook hook).
"""

from __future__ import annotations

import base64
import contextlib
import os
import tempfile
from typing import Any

import tdapi
from utils.logging import log_message
from utils.result import error_result, success_result
from utils.types import LogLevel, Result

try:  # pragma: no cover — TD provides `op`, `td`, etc. at runtime
	import td
except ImportError:  # running outside TD
	td = None  # type: ignore


class ForkService:
	"""Business logic for the td-mcp fork tools."""

	# =========================================================================
	# Editor context (Phase 3.2)
	# =========================================================================

	def get_pane(self) -> Result:
		"""Return the current network-editor pane state."""
		try:
			pane = ui.panes.current  # type: ignore  # noqa: F821
			if (
				pane is None
				or getattr(pane, "owner", None) is None
			):
				return success_result({"pane": None})

			result = {
				"path": pane.owner.path,
				"tx": getattr(pane, "x", 0),
				"ty": getattr(pane, "y", 0),
				"zoom": getattr(pane, "zoom", 1.0),
				"viewportSize": [
					getattr(pane, "width", 0),
					getattr(pane, "height", 0),
				],
			}
			return success_result(result)
		except Exception as e:
			log_message(f"get_pane failed: {e}", LogLevel.ERROR)
			return error_result(str(e))

	def get_selection(self) -> Result:
		"""Return operators currently selected in the active pane."""
		try:
			pane = ui.panes.current  # type: ignore  # noqa: F821
			if pane is None or getattr(pane, "owner", None) is None:
				return success_result({"count": 0, "ops": []})

			selected = [
				{
					"path": o.path,
					"name": o.name,
					"type": o.type,
					"opType": getattr(o, "OPType", o.type),
					"family": o.family,
					"x": o.nodeX,
					"y": o.nodeY,
				}
				for o in pane.owner.children
				if getattr(o, "selected", False) or getattr(o, "current", False)
			]
			return success_result({"count": len(selected), "ops": selected})
		except Exception as e:
			log_message(f"get_selection failed: {e}", LogLevel.ERROR)
			return error_result(str(e))

	# =========================================================================
	# Cook control (Phase 3.3)
	# =========================================================================

	def force_cook(self, path: str, recurse: bool = True) -> Result:
		"""Force-cook ``path`` (and optionally all descendants)."""
		try:
			result = tdapi.ForceCook(path, recurse=recurse)
			return success_result(result)
		except ValueError as e:
			return error_result(str(e))
		except Exception as e:
			log_message(f"force_cook failed: {e}", LogLevel.ERROR)
			return error_result(str(e))

	# =========================================================================
	# Viewport capture (Phase 3.4)
	# =========================================================================

	def capture_viewport(
		self,
		target: str,
		width: int | None = None,
		height: int | None = None,
		fmt: str = "png",
		return_as: str = "base64",
		quality: int = 85,
	) -> Result:
		"""Capture a PNG/JPG of a TOP, COMP viewer, or network editor pane.

		Args:
			target: TOP/COMP path, or ``'pane'`` for the current network editor.
			width/height: Optional resize.
			fmt: ``'png'`` or ``'jpg'``.
			return_as: ``'base64'`` (inline) or ``'path'`` (return temp path).
			quality: JPG quality (1-100, ignored for PNG).
		"""
		try:
			# Pane capture — try ui.panes[i].savePane first.
			if target == "pane":
				captured_path = self._capture_pane(fmt, width, height)
			else:
				op_ref = op(target)  # type: ignore  # noqa: F821
				if op_ref is None:
					return error_result(f"Target not found: {target}")
				captured_path = self._capture_op(
					op_ref, fmt, width, height, quality
				)

			if captured_path is None or not os.path.exists(captured_path):
				return error_result("Capture failed: no output file produced")

			size_bytes = os.path.getsize(captured_path)
			actual_width, actual_height = self._probe_image_size(captured_path)

			inline_limit = 256 * 1024  # 256 KB
			encoding: str
			data: str

			if return_as == "path" or size_bytes > inline_limit:
				encoding = "file"
				data = captured_path
			else:
				with open(captured_path, "rb") as f:
					data = base64.b64encode(f.read()).decode("ascii")
				encoding = "base64"
				# Clean up temp file if we inlined it.
				with contextlib.suppress(OSError):
					os.remove(captured_path)

			return success_result(
				{
					"format": fmt,
					"width": actual_width,
					"height": actual_height,
					"encoding": encoding,
					"data": data,
					"sizeBytes": size_bytes,
				}
			)
		except Exception as e:
			log_message(f"capture_viewport failed: {e}", LogLevel.ERROR)
			return error_result(str(e))

	def _capture_op(
		self,
		op_ref: Any,
		fmt: str,
		width: int | None,
		height: int | None,
		quality: int,
	) -> str:
		"""Capture a TOP or COMP viewer by saving the underlying TOP."""
		# For a COMP, look up its viewer TOP.
		if op_ref.family == "COMP":
			viewer = getattr(op_ref.par, "viewer", None)
			if viewer is not None and hasattr(viewer, "eval"):
				viewer_top = viewer.eval()
				if viewer_top is not None:
					op_ref = viewer_top

		if op_ref.family != "TOP":
			raise ValueError(
				f"{op_ref.path} is not a TOP or COMP with a viewer TOP"
			)

		suffix = f".{fmt}"
		tmp_fd, tmp_path = tempfile.mkstemp(
			prefix="td_mcp_viewport_", suffix=suffix
		)
		os.close(tmp_fd)

		# TD's save() handles both PNG and JPG based on extension.
		op_ref.save(tmp_path, asynchronous=False)
		# TODO Phase 4: apply width/height via a temporary fit TOP, apply JPG
		# quality via tdu parameters. Present call path leaves these as hints.
		del width, height, quality
		return tmp_path

	def _capture_pane(
		self,
		fmt: str,
		width: int | None,
		height: int | None,
	) -> str | None:
		"""Capture the current network editor pane as an image."""
		suffix = f".{fmt}"
		tmp_fd, tmp_path = tempfile.mkstemp(
			prefix="td_mcp_pane_", suffix=suffix
		)
		os.close(tmp_fd)

		pane = ui.panes.current  # type: ignore  # noqa: F821
		if pane is None:
			return None

		# Prefer savePane if available (TD 2024+).
		save_fn = getattr(pane, "savePane", None)
		if callable(save_fn):
			save_fn(tmp_path)
			del width, height
			return tmp_path

		# TODO Phase 4: fallback via temporary panelCOMP + Panel Capture TOP.
		log_message(
			"pane capture fallback not yet implemented; requires TD 2024+",
			LogLevel.WARNING,
		)
		return None

	def _probe_image_size(self, path: str) -> tuple[int, int]:
		"""Best-effort width/height probe for the captured image."""
		try:
			with open(path, "rb") as f:
				header = f.read(24)
			if header.startswith(b"\x89PNG"):
				# PNG: IHDR at bytes 16-24, width big-endian at 16:20, height 20:24
				w = int.from_bytes(header[16:20], "big")
				h = int.from_bytes(header[20:24], "big")
				return (w, h)
			if header[:3] == b"\xff\xd8\xff":
				return (0, 0)  # JPEG probing skipped — return 0 as sentinel
		except OSError:
			pass
		return (0, 0)

	# =========================================================================
	# Wiring + layout (Phase 3.5)
	# =========================================================================

	def connect_nodes(
		self,
		from_path: str,
		to_path: str,
		from_outlet: int = 0,
		to_inlet: int = 0,
	) -> Result:
		"""Wire ``from_path`` → ``to_path`` via the generic connector API.

		Compatibility is checked before connecting; incompatible families
		return a descriptive error rather than silently failing.
		"""
		try:
			src = op(from_path)  # type: ignore  # noqa: F821
			dst = op(to_path)  # type: ignore  # noqa: F821
			if src is None:
				return error_result(f"Source not found: {from_path}")
			if dst is None:
				return error_result(f"Destination not found: {to_path}")

			if from_outlet >= len(src.outputConnectors):
				return error_result(
					f"{from_path} has no outlet #{from_outlet}"
				)
			if to_inlet >= len(dst.inputConnectors):
				return error_result(
					f"{to_path} has no inlet #{to_inlet}"
				)

			# Family check: TD only allows same-family connector wiring.
			if src.family != dst.family:
				return error_result(
					f"Family mismatch: {src.family} → {dst.family} — use "
					f"a type-conversion operator (Dto CHOP, etc.) instead."
				)

			dst.inputConnectors[to_inlet].connect(src.outputConnectors[from_outlet])
			return success_result(
				{
					"ok": True,
					"from": from_path,
					"to": to_path,
					"fromOutlet": from_outlet,
					"toInlet": to_inlet,
				}
			)
		except Exception as e:
			log_message(f"connect_nodes failed: {e}", LogLevel.ERROR)
			return error_result(str(e))

	def layout_find_empty_area(
		self,
		base: str,
		width: int = 200,
		height: int = 200,
		start_x: int = 0,
		start_y: int = 0,
		margin: int = 50,
	) -> Result:
		"""Wrap :func:`tdapi.FindEmptyArea`."""
		try:
			x, y = tdapi.FindEmptyArea(
				base, width, height, start_x, start_y, margin
			)
			return success_result({"x": x, "y": y})
		except Exception as e:
			return error_result(str(e))

	def layout_check_overlap(self, op_path: str) -> Result:
		"""Return whether ``op_path`` overlaps any of its siblings."""
		try:
			target = op(op_path)  # type: ignore  # noqa: F821
			if target is None:
				return error_result(f"Not found: {op_path}")
			parent_op = target.parent()
			target_bounds = tdapi.GetBounds(target)
			sibling_bounds = [
				tdapi.GetBounds(child)
				for child in parent_op.children
				if child != target
			]
			overlaps = tdapi.CheckOverlap(target_bounds, sibling_bounds)
			return success_result({"overlaps": overlaps})
		except Exception as e:
			return error_result(str(e))

	def layout_chain(
		self, ops: list[str], spacing: int = 200
	) -> Result:
		"""Wrap :func:`tdapi.ChainOperators`."""
		try:
			resolved = []
			for path in ops:
				o = op(path)  # type: ignore  # noqa: F821
				if o is None:
					return error_result(f"Not found: {path}")
				resolved.append(o)
			tdapi.ChainOperators(resolved, spacing=spacing)
			return success_result(
				{
					"chained": [o.path for o in resolved],
					"spacing": spacing,
				}
			)
		except Exception as e:
			return error_result(str(e))

	# =========================================================================
	# GLSL authoring (Phase 3.6)
	# =========================================================================

	def glsl_read(self, path: str, stage: str) -> Result:
		"""Read the docked shader DAT for a GLSL TOP/MAT/POP."""
		try:
			op_ref = op(path)  # type: ignore  # noqa: F821
			if op_ref is None:
				return error_result(f"Not found: {path}")

			dat = self._resolve_shader_dat(op_ref, stage)
			if dat is None:
				return error_result(
					f"No {stage} shader DAT found for {path}"
				)
			return success_result(
				{
					"stage": stage,
					"docked_dat_path": dat.path,
					"code": dat.text,
					"errors": None,
				}
			)
		except Exception as e:
			log_message(f"glsl_read failed: {e}", LogLevel.ERROR)
			return error_result(str(e))

	def glsl_write(
		self,
		path: str,
		stage: str,
		code: str,
		return_compiled: bool = False,
	) -> Result:
		"""Write shader source into the correct docked DAT and re-cook."""
		try:
			op_ref = op(path)  # type: ignore  # noqa: F821
			if op_ref is None:
				return error_result(f"Not found: {path}")

			dat = self._resolve_shader_dat(op_ref, stage)
			if dat is None:
				return error_result(
					f"No {stage} shader DAT found for {path}"
				)

			dat.text = code
			op_ref.cook(force=True)

			errors: list[dict[str, Any]] | None = None
			if return_compiled:
				err_text = op_ref.errors(recurse=False)
				if err_text:
					errors = [{"line": 0, "msg": err_text}]

			return success_result(
				{
					"stage": stage,
					"docked_dat_path": dat.path,
					"code": code,
					"errors": errors,
				}
			)
		except Exception as e:
			log_message(f"glsl_write failed: {e}", LogLevel.ERROR)
			return error_result(str(e))

	def _resolve_shader_dat(self, op_ref: Any, stage: str) -> Any | None:
		"""Return the docked DAT holding ``stage`` shader source."""
		par_name_map = {
			"pixel": ["pixelshader", "pixelsrc"],
			"vertex": ["vertexshader", "vertexsrc"],
			"compute": ["computeshader", "computesrc"],
		}
		candidates = par_name_map.get(stage, [])
		for par_name in candidates:
			par = getattr(op_ref.par, par_name, None)
			if par is None:
				continue
			try:
				ref = par.eval()
			except Exception:
				continue
			if ref is not None and hasattr(ref, "text"):
				return ref
		return None

	# =========================================================================
	# Scene scaffolding (Phase 3.7)
	# =========================================================================

	def scaffold(
		self,
		template: str,
		base_path: str = "/project1",
		name_prefix: str | None = None,
	) -> Result:
		"""Scaffold a scene template under ``base_path``."""
		try:
			base = op(base_path)  # type: ignore  # noqa: F821
			if base is None:
				return error_result(f"Base path not found: {base_path}")

			prefix = name_prefix or template
			dispatch = {
				"render_pipeline": self._scaffold_render_pipeline,
				"feedback_loop": self._scaffold_feedback_loop,
				"instanced_particles": self._scaffold_instanced_particles,
				"audio_reactive": self._scaffold_audio_reactive,
				"projection_mapping": self._scaffold_projection_mapping,
			}
			handler = dispatch.get(template)
			if handler is None:
				return error_result(
					f"Unknown template: {template}. Known: {sorted(dispatch)}"
				)

			created_ops, wiring, entry_point, description = handler(base, prefix)
			tdapi.ForceCook(base.path, recurse=True)
			return success_result(
				{
					"template": template,
					"createdOps": [o.path for o in created_ops],
					"wiring": wiring,
					"entryPoint": entry_point,
					"description": description,
				}
			)
		except Exception as e:
			log_message(f"scaffold failed: {e}", LogLevel.ERROR)
			return error_result(str(e))

	def _scaffold_render_pipeline(
		self, base: Any, prefix: str
	) -> tuple[list[Any], list[dict[str, str]], str, str]:
		"""Cam + Geo + Light + Render TOP + Out TOP."""
		x, y = tdapi.FindEmptyArea(base, 900, 200)
		cam = tdapi.CreateOp(base, cameraCOMP, f"{prefix}_cam", x, y)  # noqa: F821
		geo = tdapi.CreateOp(base, geometryCOMP, f"{prefix}_geo", x, y - 200)  # noqa: F821
		light = tdapi.CreateOp(base, lightCOMP, f"{prefix}_light", x, y - 400)  # noqa: F821
		render = tdapi.CreateOp(base, renderTOP, f"{prefix}_render", x + 250, y)  # noqa: F821
		out = tdapi.CreateOp(base, outTOP, f"{prefix}_out", x + 500, y)  # noqa: F821

		render.par.camera = cam.path
		render.par.geometry = geo.path
		render.par.lights = light.path
		out.inputConnectors[0].connect(render)

		return (
			[cam, geo, light, render, out],
			[{"from": render.path, "to": out.path}],
			out.path,
			"Basic 3D render pipeline: cam + geo + light → render TOP → out.",
		)

	def _scaffold_feedback_loop(
		self, base: Any, prefix: str
	) -> tuple[list[Any], list[dict[str, str]], str, str]:
		"""Noise → comp → feedback TOP → null, looped back."""
		x, y = tdapi.FindEmptyArea(base, 900, 150)
		noise = tdapi.CreateOp(base, noiseTOP, f"{prefix}_noise", x, y)  # noqa: F821
		feedback = tdapi.CreateOp(base, feedbackTOP, f"{prefix}_fb", x + 250, y)  # noqa: F821
		comp = tdapi.CreateOp(base, compositeTOP, f"{prefix}_comp", x + 500, y)  # noqa: F821
		null_top = tdapi.CreateOp(base, nullTOP, f"{prefix}_out", x + 750, y)  # noqa: F821

		comp.inputConnectors[0].connect(noise)
		comp.inputConnectors[1].connect(feedback)
		null_top.inputConnectors[0].connect(comp)
		feedback.par.top = null_top.path  # feedback source

		return (
			[noise, feedback, comp, null_top],
			[
				{"from": noise.path, "to": comp.path},
				{"from": feedback.path, "to": comp.path},
				{"from": comp.path, "to": null_top.path},
				{"from": null_top.path, "to": feedback.path},
			],
			null_top.path,
			"Classic feedback loop: noise + feedback TOP composited and looped.",
		)

	def _scaffold_instanced_particles(
		self, base: Any, prefix: str
	) -> tuple[list[Any], list[dict[str, str]], str, str]:
		"""Grid SOP → Geo COMP → Render → Out, with instancing enabled."""
		x, y = tdapi.FindEmptyArea(base, 900, 200)
		grid = tdapi.CreateOp(base, gridSOP, f"{prefix}_grid", x, y - 200)  # noqa: F821
		geo, _in, _out = tdapi.CreateGeometryComp(
			base, f"{prefix}_geo", input_op=grid, x=x + 250, y=y
		)
		geo.par.instanceop = grid.path
		cam = tdapi.CreateOp(base, cameraCOMP, f"{prefix}_cam", x + 500, y + 200)  # noqa: F821
		render = tdapi.CreateOp(base, renderTOP, f"{prefix}_render", x + 750, y)  # noqa: F821
		out = tdapi.CreateOp(base, outTOP, f"{prefix}_out", x + 1000, y)  # noqa: F821
		render.par.geometry = geo.path
		render.par.camera = cam.path
		out.inputConnectors[0].connect(render)

		return (
			[grid, geo, cam, render, out],
			[
				{"from": grid.path, "to": geo.path},
				{"from": render.path, "to": out.path},
			],
			out.path,
			"Instanced particles scaffold: grid SOP drives a Geo COMP with "
			"instancing enabled.",
		)

	def _scaffold_audio_reactive(
		self, base: Any, prefix: str
	) -> tuple[list[Any], list[dict[str, str]], str, str]:
		"""Audio In → Analyze → Null that can drive any TOP param."""
		x, y = tdapi.FindEmptyArea(base, 900, 150)
		audio = tdapi.CreateOp(base, audiodeviceinCHOP, f"{prefix}_audio", x, y)  # noqa: F821
		analyze = tdapi.CreateOp(base, analyzeCHOP, f"{prefix}_analyze", x + 250, y)  # noqa: F821
		null_chop = tdapi.CreateOp(base, nullCHOP, f"{prefix}_out", x + 500, y)  # noqa: F821
		analyze.inputConnectors[0].connect(audio)
		null_chop.inputConnectors[0].connect(analyze)

		return (
			[audio, analyze, null_chop],
			[
				{"from": audio.path, "to": analyze.path},
				{"from": analyze.path, "to": null_chop.path},
			],
			null_chop.path,
			"Audio-reactive scaffold: Audio Device In → Analyze → Null CHOP. "
			"Reference the Null CHOP's channels from any TOP parameter "
			"(e.g. `op('audio_out')['chan1']`).",
		)

	def _scaffold_projection_mapping(
		self, base: Any, prefix: str
	) -> tuple[list[Any], list[dict[str, str]], str, str]:
		"""Minimal projection mapping scaffold: content → transform → out."""
		x, y = tdapi.FindEmptyArea(base, 900, 150)
		content = tdapi.CreateOp(
			base, constantTOP, f"{prefix}_content", x, y
		)  # noqa: F821
		transform = tdapi.CreateOp(
			base, transformTOP, f"{prefix}_xform", x + 250, y
		)  # noqa: F821
		out = tdapi.CreateOp(
			base, outTOP, f"{prefix}_out", x + 500, y
		)  # noqa: F821
		transform.inputConnectors[0].connect(content)
		out.inputConnectors[0].connect(transform)

		return (
			[content, transform, out],
			[
				{"from": content.path, "to": transform.path},
				{"from": transform.path, "to": out.path},
			],
			out.path,
			"Projection mapping scaffold: constant → transform → out. "
			"Replace the Constant TOP with your content source and drive "
			"Transform TOP parameters from a mapping UI.",
		)
