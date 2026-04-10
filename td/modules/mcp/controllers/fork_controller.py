"""
Fork controller — HTTP routing for td-mcp fork-specific endpoints.

All fork routes live under the ``/fork/*`` prefix so they cannot collide
with upstream's OpenAPI-generated routes. This controller wraps the
upstream ``api_controller_openapi`` and handles fork paths first,
falling through to upstream for anything it doesn't recognize.

URL map (all methods are POST with a JSON body unless noted):

=================================  ==================================
Route                              Service method
=================================  ==================================
``GET  /fork/editor/pane``         :meth:`ForkService.get_pane`
``GET  /fork/editor/selection``    :meth:`ForkService.get_selection`
``POST /fork/cook``                :meth:`ForkService.force_cook`
``POST /fork/viewport``            :meth:`ForkService.capture_viewport`
``POST /fork/connect``             :meth:`ForkService.connect_nodes`
``POST /fork/layout/find_empty``   :meth:`ForkService.layout_find_empty_area`
``POST /fork/layout/overlap``      :meth:`ForkService.layout_check_overlap`
``POST /fork/layout/chain``        :meth:`ForkService.layout_chain`
``POST /fork/glsl/read``           :meth:`ForkService.glsl_read`
``POST /fork/glsl/write``          :meth:`ForkService.glsl_write`
``POST /fork/scaffold``            :meth:`ForkService.scaffold`
=================================  ==================================
"""

from __future__ import annotations

import json
import traceback
from typing import Any

from mcp.services.fork_service import ForkService
from utils.logging import log_message
from utils.types import LogLevel, Result


def _ok(response: dict[str, Any], data: Any) -> dict[str, Any]:
	response["statusCode"] = 200
	response["statusReason"] = "OK"
	response["headers"] = {"Content-Type": "application/json"}
	response["body"] = json.dumps({"success": True, "data": data})
	return response


def _err(
	response: dict[str, Any],
	status: int,
	message: str,
) -> dict[str, Any]:
	response["statusCode"] = status
	response["statusReason"] = "Error"
	response["headers"] = {"Content-Type": "application/json"}
	response["body"] = json.dumps({"success": False, "error": message})
	return response


def _parse_body(request: dict[str, Any]) -> dict[str, Any]:
	"""Extract JSON body from a TD WebServer DAT request object."""
	raw = request.get("data") or request.get("body") or "{}"
	if isinstance(raw, bytes):
		raw = raw.decode("utf-8")
	if not raw or not raw.strip():
		return {}
	try:
		return json.loads(raw)
	except json.JSONDecodeError:
		return {}


def _result_to_response(
	result: Result,
	response: dict[str, Any],
) -> dict[str, Any]:
	"""Convert a service Result into an HTTP response."""
	if result.success:
		return _ok(response, result.data)
	return _err(response, 500, str(result.error) if result.error else "error")


class ForkController:
	"""HTTP controller for ``/fork/*`` routes."""

	def __init__(self, upstream_controller: Any) -> None:
		self.upstream = upstream_controller
		self.service = ForkService()

	def onHTTPRequest(  # noqa: N802 — TD callback naming
		self,
		webServerDAT: Any,  # noqa: N803
		request: dict[str, Any],
		response: dict[str, Any],
	) -> dict[str, Any]:
		uri = request.get("uri", "") or ""
		method = (request.get("method") or "GET").upper()

		if not uri.startswith("/fork/"):
			return self.upstream.onHTTPRequest(webServerDAT, request, response)

		try:
			return self._dispatch(uri, method, request, response)
		except Exception as e:
			log_message(
				f"ForkController error on {method} {uri}: {e}\n{traceback.format_exc()}",
				LogLevel.ERROR,
			)
			return _err(response, 500, str(e))

	def _dispatch(
		self,
		uri: str,
		method: str,
		request: dict[str, Any],
		response: dict[str, Any],
	) -> dict[str, Any]:
		body = _parse_body(request) if method != "GET" else {}
		svc = self.service

		if uri == "/fork/editor/pane" and method == "GET":
			return _result_to_response(svc.get_pane(), response)

		if uri == "/fork/editor/selection" and method == "GET":
			return _result_to_response(svc.get_selection(), response)

		if uri == "/fork/cook" and method == "POST":
			return _result_to_response(
				svc.force_cook(
					body.get("path", "/"),
					recurse=bool(body.get("recurse", True)),
				),
				response,
			)

		if uri == "/fork/viewport" and method == "POST":
			return _result_to_response(
				svc.capture_viewport(
					target=body.get("target", ""),
					width=body.get("width"),
					height=body.get("height"),
					fmt=body.get("format", "png"),
					return_as=body.get("returnAs", "base64"),
					quality=int(body.get("quality", 85)),
				),
				response,
			)

		if uri == "/fork/connect" and method == "POST":
			return _result_to_response(
				svc.connect_nodes(
					from_path=body.get("from", ""),
					to_path=body.get("to", ""),
					from_outlet=int(body.get("fromOutlet", 0)),
					to_inlet=int(body.get("toInlet", 0)),
				),
				response,
			)

		if uri == "/fork/layout/find_empty" and method == "POST":
			return _result_to_response(
				svc.layout_find_empty_area(
					base=body.get("base", "/project1"),
					width=int(body.get("width", 200)),
					height=int(body.get("height", 200)),
					start_x=int(body.get("startX", 0)),
					start_y=int(body.get("startY", 0)),
					margin=int(body.get("margin", 50)),
				),
				response,
			)

		if uri == "/fork/layout/overlap" and method == "POST":
			return _result_to_response(
				svc.layout_check_overlap(op_path=body.get("op", "")),
				response,
			)

		if uri == "/fork/layout/chain" and method == "POST":
			ops_list = body.get("ops") or []
			if not isinstance(ops_list, list):
				return _err(response, 400, "'ops' must be a list of op paths")
			return _result_to_response(
				svc.layout_chain(
					ops=[str(o) for o in ops_list],
					spacing=int(body.get("spacing", 200)),
				),
				response,
			)

		if uri == "/fork/glsl/read" and method == "POST":
			return _result_to_response(
				svc.glsl_read(
					path=body.get("path", ""),
					stage=body.get("stage", "pixel"),
				),
				response,
			)

		if uri == "/fork/glsl/write" and method == "POST":
			return _result_to_response(
				svc.glsl_write(
					path=body.get("path", ""),
					stage=body.get("stage", "pixel"),
					code=body.get("code", ""),
					return_compiled=bool(body.get("returnCompiled", False)),
				),
				response,
			)

		if uri == "/fork/scaffold" and method == "POST":
			return _result_to_response(
				svc.scaffold(
					template=body.get("template", ""),
					base_path=body.get("base", "/project1"),
					name_prefix=body.get("name"),
				),
				response,
			)

		return _err(response, 404, f"Unknown fork route: {method} {uri}")
