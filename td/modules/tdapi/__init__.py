"""
tdapi — TouchDesigner helper library for AI agents.

This module exposes a small but opinionated set of helpers that the td-mcp
server (and the Python code an AI agent runs via ``execute_python_script``)
should prefer over raw TD calls. The helpers handle three recurring pain
points that trip up naive automation:

1. **Docked operators.** When you create a ``glslTOP``, TD auto-creates
   ``_pixel_shader`` and ``_vertex_shader`` DATs docked to the parent.
   Tools that set ``nodeX``/``nodeY`` directly on the parent orphan them.
   :func:`CreateOp` and :func:`MoveOp` handle docked ops as a unit.

2. **Layout intelligence.** Dropping every new op at (0, 0) produces a
   pile. :func:`FindEmptyArea` and :func:`CheckOverlap` let callers
   request non-overlapping placement with a consistent margin.

3. **Introspection before mutation.** TD parameter names are notoriously
   non-obvious (``radx`` vs ``radius``). :func:`GetParameterList` and
   :func:`GetParameterHelp` push the caller (and the LLM driving it)
   toward verification before setting parameters.

The module also adds one fork-specific helper — :func:`ForceCook` —
that addresses the nested ``baseCOMP`` cooking bug documented in
``docs/roadmap.md#td_cook``.

## Usage

All helpers are module-level functions (no ``self``), so you can use
them directly from an ``execute_python_script`` call::

    import tdapi
    tdapi.CreateOp(op("/project1"), boxSOP, "box1", 100, 100)
    x, y = tdapi.FindEmptyArea(op("/project1"), 200, 200)

A companion :class:`TDAPIExtension` class wraps the same functions for
eventual use as a TouchDesigner COMP extension (allowing the
``op.TDAPI.CreateOp(...)`` access pattern once the ``.tox`` is updated
to ship a COMP named ``TDAPI`` with this extension attached).

## Attribution

The core helpers (``MoveOp``, ``CreateOp``, ``CreateGeometryComp``,
``ChainOperators``, ``GetBounds``, ``CheckOverlap``, ``GetAllBounds``,
``FindEmptyArea``, ``FindTypeConversionPosition``, ``GetOperatorInfo``,
``GetParameterList``, ``GetParameterHelp``, ``PrintLayout``,
``CheckErrors``) are ported from
`satoruhiga/claude-touchdesigner <https://github.com/satoruhiga/claude-touchdesigner>`_
(MIT License). The ``self`` parameter from the upstream class-method
form has been stripped; everything else preserves upstream semantics.

``ForceCook`` is a fork addition.
"""

# Based on satoruhiga/claude-touchdesigner (MIT)
# https://github.com/satoruhiga/claude-touchdesigner/blob/main/touchdesigner/toe/src/td_utils.py

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any, NamedTuple

if TYPE_CHECKING:
	from typing import TypeAlias

	OP: TypeAlias = Any  # TouchDesigner operator type


__all__ = [
	"AABB",
	"ChainOperators",
	"CheckErrors",
	"CheckOverlap",
	"CreateGeometryComp",
	"CreateOp",
	"FindEmptyArea",
	"FindTypeConversionPosition",
	"ForceCook",
	"GetAllBounds",
	"GetBounds",
	"GetOperatorInfo",
	"GetParameterHelp",
	"GetParameterList",
	"MoveOp",
	"PrintLayout",
]


class AABB(NamedTuple):
	"""Axis-Aligned Bounding Box used by the layout helpers."""

	min_x: int
	min_y: int
	max_x: int
	max_y: int

	@property
	def width(self) -> int:
		return self.max_x - self.min_x

	@property
	def height(self) -> int:
		return self.max_y - self.min_y

	@property
	def x(self) -> int:
		return self.min_x

	@property
	def y(self) -> int:
		return self.min_y


# =============================================================================
# Creation + movement (docked-operator aware)
# =============================================================================


def MoveOp(target: OP | str, x: int, y: int) -> OP:
	"""Move an operator, keeping docked operators in formation.

	Args:
		target: Operator instance or path string.
		x: Target X position.
		y: Target Y position.

	Returns:
		The moved operator.
	"""
	if isinstance(target, str):
		target = op(target)  # noqa: F821

	dx = x - target.nodeX
	dy = y - target.nodeY

	# Move docked operators first to preserve their relative offset.
	for d in target.docked:
		d.nodeX += dx
		d.nodeY += dy

	target.nodeX = x
	target.nodeY = y
	return target


def CreateOp(
	base: OP | str,
	op_type: type,
	name: str,
	x: int | None = None,
	y: int | None = None,
) -> OP:
	"""Create an operator with ``viewer=True`` and optional layout.

	If an operator with the same name already exists, TD auto-increments
	the name (``null1`` → ``null2``); the actually-created operator is
	returned so callers can check ``.name`` if they care.

	Args:
		base: Parent operator instance or path string.
		op_type: Operator type constant (e.g. ``boxSOP``, ``glslTOP``).
		name: Desired operator name.
		x: Optional X position; if supplied, MoveOp is used so that
			docked DATs follow the parent.
		y: Optional Y position.

	Returns:
		The newly created operator.
	"""
	if isinstance(base, str):
		base = op(base)  # noqa: F821

	new_op = base.create(op_type, name)
	new_op.viewer = True

	if x is not None and y is not None:
		MoveOp(new_op, x, y)

	return new_op


def CreateGeometryComp(
	base: OP | str,
	name: str,
	input_op: OP | None = None,
	x: int | None = None,
	y: int | None = None,
) -> tuple[OP, OP, OP]:
	"""Scaffold a Geometry COMP with In/Out SOP (or POP) already wired.

	The default torus is removed, In/Out operators are created based on
	the family of ``input_op`` (SOP by default, POP if an ``input_op``
	of family ``'POP'`` is supplied), wired, and set to display/render.

	Args:
		base: Parent operator instance or path string.
		name: Name for the new Geometry COMP.
		input_op: Optional SOP/POP whose output is connected to the
			COMP's external input connector.
		x: Optional X position.
		y: Optional Y position.

	Returns:
		Tuple of (geo_comp, in_op, out_op).
	"""
	if isinstance(base, str):
		base = op(base)  # noqa: F821

	family = "SOP"
	if input_op is not None:
		family = input_op.family

	geo = CreateOp(base, geometryCOMP, name, x, y)  # noqa: F821

	# Remove default torus.
	for child in geo.children:
		child.destroy()

	if family == "POP":
		in_op = geo.create(inPOP, "in1")  # noqa: F821
		out_op = geo.create(outPOP, "out1")  # noqa: F821
	else:
		in_op = geo.create(inSOP, "in1")  # noqa: F821
		out_op = geo.create(outSOP, "out1")  # noqa: F821

	in_op.viewer = True
	out_op.viewer = True
	out_op.inputConnectors[0].connect(in_op)
	out_op.display = True
	out_op.render = True

	if input_op is not None:
		geo.inputConnectors[0].connect(input_op)

	return geo, in_op, out_op


def ChainOperators(operators: list[OP], spacing: int = 200) -> list[OP]:
	"""Connect operators in sequence and lay them out horizontally.

	Uses ``inputConnectors`` (same-family chain). Each operator is
	positioned ``spacing`` pixels to the right of its predecessor.

	Args:
		operators: Ordered list of operators to chain.
		spacing: Horizontal gap in pixels (default 200).

	Returns:
		The same ``operators`` list, for convenient chaining.

	Note:
		For cross-family connections (SOP → CHOP, etc.) you should
		drive the destination's ``par.sop``/``par.chop`` reference
		directly — conversion operators do not use ``inputConnectors``.
	"""
	if not operators:
		return []

	for i in range(1, len(operators)):
		prev_op = operators[i - 1]
		curr_op = operators[i]
		curr_op.inputConnectors[0].connect(prev_op)
		MoveOp(curr_op, prev_op.nodeX + spacing, prev_op.nodeY)

	return operators


# =============================================================================
# Introspection (parameters + operator metadata)
# =============================================================================


_help_data_cache: dict[str, Any] | None = None


def _get_help_data() -> dict[str, Any]:
	"""Load TD's built-in help data (internal, cached)."""
	global _help_data_cache
	if _help_data_cache is None:
		import json

		_help_data_cache = json.loads(
			op("/ui/dialogs/parGrabber/offlineHelp").text  # noqa: F821
		)
	assert _help_data_cache is not None
	return _help_data_cache


def _get_family_key(op_type: str) -> str | None:
	"""Map an operator type suffix to its help family key."""
	family_map = {
		"SOP": "SOPs",
		"POP": "POPs",
		"TOP": "TOPs",
		"CHOP": "CHOPs",
		"DAT": "DATs",
		"COMP": "COMPs",
		"MAT": "MATs",
	}
	for suffix, family_key in family_map.items():
		if op_type.endswith(suffix):
			return family_key
	return None


def GetOperatorInfo(op_type: str) -> dict[str, Any] | None:
	"""Look up an operator type in TD's built-in help data.

	Args:
		op_type: Operator type name (e.g. ``'spherePOP'``, ``'glslTOP'``).

	Returns:
		Dict with ``summary``, ``label``, ``parameters`` keys, or
		``None`` if no match is found.
	"""
	help_data = _get_help_data()
	family_key = _get_family_key(op_type)
	if family_key:
		return help_data["help"].get(family_key, {}).get(op_type)
	return None


def GetParameterList(op_type: str) -> list[str]:
	"""Return the parameter names for an operator type.

	Prefer this over the LLM's prior knowledge of TD parameter names —
	``radius`` vs ``radx``/``rady``/``radz`` is a common trap.

	Args:
		op_type: Operator type name.

	Returns:
		List of parameter names (empty if unknown).
	"""
	info = GetOperatorInfo(op_type)
	if info and "parameters" in info:
		return list(info["parameters"].keys())
	return []


def GetParameterHelp(op_type: str, param_name: str) -> dict[str, Any] | None:
	"""Return TD's help entry for a specific parameter.

	Args:
		op_type: Operator type name.
		param_name: Parameter name.

	Returns:
		Parameter info dict or ``None``.
	"""
	info = GetOperatorInfo(op_type)
	if info and "parameters" in info:
		return info["parameters"].get(param_name)
	return None


def PrintLayout(base: OP | str) -> None:
	"""Print children of ``base`` sorted by (nodeY, nodeX) for debugging.

	Args:
		base: Parent operator instance or path string. Unlike the
			upstream ``PrintLayout``, a ``base`` argument is required
			here (there's no ``self.ownerComp`` fallback in module-level
			form).
	"""
	if isinstance(base, str):
		base = op(base)  # noqa: F821

	for child in sorted(base.children, key=lambda c: (c.nodeY, c.nodeX)):
		print(f"{child.name}: ({child.nodeX}, {child.nodeY}) [{child.family}]")


# =============================================================================
# Errors
# =============================================================================


def CheckErrors(target: OP | str, recurse: bool = True) -> str:
	"""Force-cook ``target`` and return any errors as a string.

	.. warning::

		TouchDesigner updates its error cache **only on frame
		boundaries**. A sequence of "mutate the op, immediately check
		errors" may return stale data from inside a single
		``execute_python_script`` call. Safe pattern: do the mutation
		in one ``execute_python_script`` call and the error check in a
		second, subsequent call.

	Args:
		target: Operator instance or path string (required).
		recurse: Also check child errors recursively.

	Returns:
		Error string, empty if none.

	Raises:
		ValueError: If ``target`` is ``None`` or an invalid path.
	"""
	if target is None:
		raise ValueError("target is required and cannot be None")

	if isinstance(target, str):
		resolved = op(target)  # noqa: F821
		if resolved is None:
			raise ValueError(f"Invalid operator path: {target}")
		target = resolved

	target.cook(force=True)
	errors = target.errors(recurse=recurse)
	if errors:
		print(f"Errors in {target.path}: {errors}")
	return errors


# =============================================================================
# Layout
# =============================================================================


def GetBounds(target: OP | str | list[OP | str]) -> AABB:
	"""Return a bounding box that includes ``target``'s docked operators.

	Args:
		target: Operator instance, path string, or list of the above.

	Returns:
		:class:`AABB` with ``min_x``, ``min_y``, ``max_x``, ``max_y``
		and convenience ``width``/``height``/``x``/``y`` properties.
	"""
	if isinstance(target, list):
		if not target:
			return AABB(0, 0, 0, 0)
		all_bounds = [GetBounds(t) for t in target]
		return AABB(
			min(b.min_x for b in all_bounds),
			min(b.min_y for b in all_bounds),
			max(b.max_x for b in all_bounds),
			max(b.max_y for b in all_bounds),
		)

	if isinstance(target, str):
		target = op(target)  # noqa: F821

	min_x = target.nodeX
	min_y = target.nodeY
	max_x = target.nodeX + target.nodeWidth
	max_y = target.nodeY + target.nodeHeight

	for d in target.docked:
		min_x = min(min_x, d.nodeX)
		min_y = min(min_y, d.nodeY)
		max_x = max(max_x, d.nodeX + d.nodeWidth)
		max_y = max(max_y, d.nodeY + d.nodeHeight)

	return AABB(min_x, min_y, max_x, max_y)


def _aabb_overlap(b1: AABB, b2: AABB) -> bool:
	"""AABB overlap test (internal)."""
	return not (
		b1.max_x <= b2.min_x
		or b2.max_x <= b1.min_x
		or b1.max_y <= b2.min_y
		or b2.max_y <= b1.min_y
	)


def CheckOverlap(
	bounds1: AABB | list[AABB],
	bounds2: AABB | list[AABB],
) -> bool:
	"""Return True if any bounds in ``bounds1`` overlap any in ``bounds2``.

	Accepts a single :class:`AABB` or a list on either side.
	"""
	list1 = [bounds1] if isinstance(bounds1, AABB) else list(bounds1)
	list2 = [bounds2] if isinstance(bounds2, AABB) else list(bounds2)

	for b1 in list1:
		for b2 in list2:
			if _aabb_overlap(b1, b2):
				return True
	return False


def GetAllBounds(base: OP | str) -> list[AABB]:
	"""Return bounds for every child of ``base``.

	Args:
		base: Container operator or path string.
	"""
	if isinstance(base, str):
		base = op(base)  # noqa: F821
	return [GetBounds(child) for child in base.children]


def FindEmptyArea(
	base: OP | str,
	width: int,
	height: int,
	start_x: int = 0,
	start_y: int = 0,
	margin: int = 50,
) -> tuple[int, int]:
	"""Return an ``(x, y)`` that fits a ``width × height`` block
	without overlapping any existing child of ``base``.

	Algorithm:

	1. Generate candidate positions: the requested start, plus positions
	   adjacent to every existing op (right / above / below).
	2. Sort candidates, preferring those closer to ``start_x`` then
	   ``start_y``.
	3. Return the first non-overlapping candidate.
	4. Fallback: rightmost existing op + ``margin``.

	Args:
		base: Container operator or path string.
		width: Required width (including any docked operators).
		height: Required height (including any docked operators).
		start_x: Preferred start X.
		start_y: Preferred start Y.
		margin: Space to leave between operators.
	"""
	if isinstance(base, str):
		base = op(base)  # noqa: F821

	all_bounds = GetAllBounds(base)
	if not all_bounds:
		return (start_x, start_y)

	candidates: list[tuple[int, int]] = [(start_x, start_y)]

	for b in all_bounds:
		candidates.append((b.max_x + margin, b.min_y))
		candidates.append((b.min_x, b.max_y + margin))
		candidates.append((b.min_x, b.min_y - height - margin))

	candidates.sort(key=lambda c: (abs(c[0] - start_x), abs(c[1] - start_y)))

	for (x, y) in candidates:
		candidate_bounds = AABB(x, y, x + width, y + height)
		if not CheckOverlap(candidate_bounds, all_bounds):
			return (x, y)

	rightmost = max(b.max_x for b in all_bounds)
	return (rightmost + margin, start_y)


def FindTypeConversionPosition(
	source_op: OP | str,
	target_width: int,
	target_height: int,
	direction: str = "auto",
	margin: int = 40,
) -> tuple[int, int]:
	"""Find a good spot next to ``source_op`` for a type-conversion op.

	Places the new operator at the same X as the source, shifted
	vertically. If both ``up`` and ``down`` overlap existing ops, shifts
	X to the right in 200-pixel increments.

	Args:
		source_op: Source operator instance or path string.
		target_width: Width of the new operator (including docked).
		target_height: Height of the new operator (including docked).
		direction: ``'up'``, ``'down'``, or ``'auto'`` (prefer whichever
			collides less).
		margin: Space between operators.
	"""
	if isinstance(source_op, str):
		source_op = op(source_op)  # noqa: F821

	source_bounds = GetBounds(source_op)
	base = source_op.parent()
	all_bounds = GetAllBounds(base)
	all_bounds = [b for b in all_bounds if b != source_bounds]

	source_x = source_bounds.min_x
	pos_above = (source_x, source_bounds.max_y + margin)
	pos_below = (source_x, source_bounds.min_y - target_height - margin)

	if direction == "up":
		candidates = [pos_above, pos_below]
	elif direction == "down":
		candidates = [pos_below, pos_above]
	else:  # auto
		bounds_above = AABB(
			pos_above[0],
			pos_above[1],
			pos_above[0] + target_width,
			pos_above[1] + target_height,
		)
		bounds_below = AABB(
			pos_below[0],
			pos_below[1],
			pos_below[0] + target_width,
			pos_below[1] + target_height,
		)

		overlap_above = (
			CheckOverlap(bounds_above, all_bounds) if all_bounds else False
		)
		overlap_below = (
			CheckOverlap(bounds_below, all_bounds) if all_bounds else False
		)

		if not overlap_above:
			return pos_above
		if not overlap_below:
			return pos_below
		candidates = [pos_above, pos_below]

	for (x, y) in candidates:
		for x_offset in range(0, 1000, 200):
			test_bounds = AABB(
				x + x_offset,
				y,
				x + x_offset + target_width,
				y + target_height,
			)
			if not all_bounds or not CheckOverlap(test_bounds, all_bounds):
				return (x + x_offset, y)

	return pos_above


# =============================================================================
# Cook control (fork addition)
# =============================================================================


def ForceCook(target: OP | str, recurse: bool = True) -> dict[str, Any]:
	"""Force-cook ``target`` (and optionally its descendants).

	Fixes the nested-``baseCOMP`` staleness bug: operators inside a
	nested ``baseCOMP`` don't cook automatically when referenced
	indirectly. Calling ``ForceCook`` on the container restores sanity.

	This is a **fork addition** (not in the upstream
	satoruhiga/claude-touchdesigner source) and is the implementation
	target for the ``td_cook`` MCP tool described in
	``docs/roadmap.md#td_cook``.

	Args:
		target: Operator instance or path string. Use ``'/'`` for the
			project root.
		recurse: If True (default), also cook all descendants.

	Returns:
		Dict with keys:

		- ``cooked``: Count of operators successfully cooked.
		- ``totalCookTimeMs``: Wall-clock elapsed time in milliseconds.
		- ``errors``: List of ``{path, msg}`` for each operator that
			raised during cook.
	"""
	if target is None:
		raise ValueError("target is required and cannot be None")

	if isinstance(target, str):
		resolved = op(target)  # noqa: F821
		if resolved is None:
			raise ValueError(f"Invalid operator path: {target}")
		target = resolved

	start = time.perf_counter()
	cooked = 0
	errors: list[dict[str, str]] = []

	targets: list[Any] = []
	if recurse and hasattr(target, "findChildren"):
		try:
			targets = list(target.findChildren())
		except Exception as e:
			errors.append({"path": getattr(target, "path", "?"), "msg": str(e)})
	targets.append(target)

	for o in targets:
		try:
			o.cook(force=True)
			cooked += 1
		except Exception as e:
			errors.append({"path": getattr(o, "path", "?"), "msg": str(e)})

	elapsed_ms = (time.perf_counter() - start) * 1000
	return {
		"cooked": cooked,
		"totalCookTimeMs": elapsed_ms,
		"errors": errors,
	}
