"""
TDAPIExtension — thin class wrapper around the :mod:`tdapi` module.

Attach this as a TouchDesigner COMP extension (e.g. on a ``baseCOMP``
named ``TDAPI``) so that AI agents can access the helpers via the
``op.TDAPI.CreateOp(...)`` pattern, matching the design described in
``docs/roadmap.md#optdapi-python-helper-library``.

## Usage inside TouchDesigner

1. Create (or open the existing) ``mcp_webserver_base.tox``.
2. Add a ``baseCOMP`` named ``TDAPI``.
3. On that COMP, set an extension whose class is
   ``tdapi.extension.TDAPIExtension``.
4. Promote the extension so it's accessible as ``op('/.../TDAPI').ext``
   or via a shortcut.

This class keeps a very thin surface — each method simply delegates to
the corresponding module-level function in :mod:`tdapi`. If you're
writing Python inside an ``execute_python_script`` call and you don't
need the extension-style access, prefer ``import tdapi`` directly.

## Attribution

Shape of the class mirrors
`satoruhiga/claude-touchdesigner <https://github.com/satoruhiga/claude-touchdesigner>`_
(MIT License), which bound helper functions to a
``TouchDesignerAPI`` extension class. The implementations live in
:mod:`tdapi` rather than being duplicated here.
"""

# Based on satoruhiga/claude-touchdesigner (MIT)
# https://github.com/satoruhiga/claude-touchdesigner/blob/main/touchdesigner/toe/src/TouchDesignerAPI.py

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from . import (
	AABB,
	ChainOperators,
	CheckErrors,
	CheckOverlap,
	CreateGeometryComp,
	CreateOp,
	FindEmptyArea,
	FindTypeConversionPosition,
	ForceCook,
	GetAllBounds,
	GetBounds,
	GetOperatorInfo,
	GetParameterHelp,
	GetParameterList,
	MoveOp,
	PrintLayout,
)

if TYPE_CHECKING:
	from typing import TypeAlias

	OP: TypeAlias = Any


class TDAPIExtension:
	"""Class wrapper around the :mod:`tdapi` helpers.

	Binds every public function in :mod:`tdapi` as a method so TD users
	can access them via the ``op.TDAPI.CreateOp(...)`` style after
	attaching this class as an extension on a COMP named ``TDAPI``.
	"""

	def __init__(self, ownerComp):  # noqa: N803
		self.ownerComp = ownerComp

	# --- creation / movement ------------------------------------------------

	def CreateOp(
		self,
		base: OP | str,
		op_type: type,
		name: str,
		x: int | None = None,
		y: int | None = None,
	) -> OP:
		return CreateOp(base, op_type, name, x, y)

	def CreateGeometryComp(
		self,
		base: OP | str,
		name: str,
		input_op: OP | None = None,
		x: int | None = None,
		y: int | None = None,
	) -> tuple[OP, OP, OP]:
		return CreateGeometryComp(base, name, input_op, x, y)

	def ChainOperators(self, operators: list[OP], spacing: int = 200) -> list[OP]:
		return ChainOperators(operators, spacing)

	def MoveOp(self, target: OP | str, x: int, y: int) -> OP:
		return MoveOp(target, x, y)

	# --- introspection ------------------------------------------------------

	def GetOperatorInfo(self, op_type: str) -> dict[str, Any] | None:
		return GetOperatorInfo(op_type)

	def GetParameterList(self, op_type: str) -> list[str]:
		return GetParameterList(op_type)

	def GetParameterHelp(
		self, op_type: str, param_name: str
	) -> dict[str, Any] | None:
		return GetParameterHelp(op_type, param_name)

	def PrintLayout(self, base: OP | str | None = None) -> None:
		if base is None:
			base = self.ownerComp.parent()
		return PrintLayout(base)

	# --- errors -------------------------------------------------------------

	def CheckErrors(self, target: OP | str, recurse: bool = True) -> str:
		return CheckErrors(target, recurse)

	# --- layout -------------------------------------------------------------

	def GetBounds(self, target: OP | str | list[OP | str]) -> AABB:
		return GetBounds(target)

	def GetAllBounds(self, base: OP | str) -> list[AABB]:
		return GetAllBounds(base)

	def CheckOverlap(
		self,
		bounds1: AABB | list[AABB],
		bounds2: AABB | list[AABB],
	) -> bool:
		return CheckOverlap(bounds1, bounds2)

	def FindEmptyArea(
		self,
		base: OP | str,
		width: int,
		height: int,
		start_x: int = 0,
		start_y: int = 0,
		margin: int = 50,
	) -> tuple[int, int]:
		return FindEmptyArea(base, width, height, start_x, start_y, margin)

	def FindTypeConversionPosition(
		self,
		source_op: OP | str,
		target_width: int,
		target_height: int,
		direction: str = "auto",
		margin: int = 40,
	) -> tuple[int, int]:
		return FindTypeConversionPosition(
			source_op, target_width, target_height, direction, margin
		)

	# --- cook control (fork addition) --------------------------------------

	def ForceCook(
		self, target: OP | str, recurse: bool = True
	) -> dict[str, Any]:
		return ForceCook(target, recurse)
