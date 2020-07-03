# Copyright (C) 2019-2020, TomTom (http://tomtom.com).
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Base classes and functionality for transcoding."""

from abc import ABC
from typing import Optional, TypeVar

from ..generator.errors import AsciiDocError
from ..model import (Compound, EnumValue, InnerTypeReference, Member, Parameter, ReferableElement,
                     ReturnValue, ThrowsClause, TypeRef, TypeRefBase)


class TranscoderError(AsciiDocError):
    """Error encountered in transcoding.

    Args:
        msg: Message explaining the transcoder error.
    """
    msg: str

    def __init__(self, msg: str):
        self.msg = msg

    def __str__(self) -> str:
        return f"Transcoding failed: {self.msg}"


class TranscoderBase(ABC):
    SOURCE: str
    TARGET: str

    def compound(self, compound: Compound) -> Compound:
        # TODO update ApiReference

        transcoded = self.referable_element(compound)

        transcoded.members = [self.member(m) for m in compound.members]
        transcoded.inner_classes = [
            self.inner_type_reference(itr) for itr in compound.inner_classes
        ]
        transcoded.brief = compound.brief
        transcoded.description = compound.description
        transcoded.enumvalues = [self.enum_value(ev) for ev in compound.enumvalues]
        transcoded.include = compound.include
        transcoded.namespace = compound.namespace

        return transcoded

    def member(self, member: Member) -> Member:
        # TODO update ApiReference

        transcoded = self.referable_element(member)

        transcoded.definition = member.definition
        transcoded.args = member.args
        transcoded.params = [self.parameter(a) for a in member.params]
        transcoded.exceptions = [self.throws_clause(e) for e in member.exceptions]
        transcoded.brief = member.brief
        transcoded.description = member.description
        transcoded.prot = member.prot
        transcoded.returns = self.return_value(member.returns) if member.returns else None
        transcoded.enumvalues = [self.enum_value(ev) for ev in member.enumvalues]
        transcoded.static = member.static
        transcoded.include = member.include
        transcoded.namespace = member.namespace

        return transcoded

    def type_ref(self, type_ref: TypeRef) -> TypeRef:
        transcoded = self.type_ref_base(type_ref)

        transcoded.kind = type_ref.kind
        transcoded.prefix = type_ref.prefix
        transcoded.suffix = type_ref.suffix
        transcoded.nested = [self.type_ref(tr)
                             for tr in type_ref.nested] if type_ref.nested else None
        transcoded.args = [self.parameter(a) for a in type_ref.args] if type_ref.args else None

        return transcoded

    def parameter(self, parameter: Parameter) -> Parameter:
        transcoded = Parameter()

        transcoded.type = self.type_ref(parameter.type) if parameter.type else None
        transcoded.name = parameter.name
        transcoded.description = parameter.description

        return transcoded

    def return_value(self, return_value: ReturnValue) -> ReturnValue:
        transcoded = ReturnValue()

        transcoded.type = self.type_ref(return_value.type) if return_value.type else None
        transcoded.description = return_value.description

        return transcoded

    def throws_clause(self, throws_clause: ThrowsClause) -> ThrowsClause:
        transcoded = ThrowsClause(self.TARGET)

        transcoded.type = self.type_ref(throws_clause.type)
        transcoded.description = throws_clause.description

        return transcoded

    def enum_value(self, enum_value: EnumValue) -> EnumValue:
        # TODO update ApiReference

        transcoded = self.referable_element(enum_value)

        transcoded.initializer = enum_value.initializer
        transcoded.brief = enum_value.brief
        transcoded.description = enum_value.description

        return transcoded

    def inner_type_reference(self, ref: InnerTypeReference) -> InnerTypeReference:
        transcoded = self.type_ref_base(ref)

        if ref.referred_object is not None:
            transcoded.referred_object = self.compound(ref.referred_object)

        return transcoded

    def convert_id(self, old_id: Optional[str]) -> Optional[str]:
        if not old_id:
            return old_id

        if old_id.startswith(f"{self.SOURCE}-"):
            old_id = old_id[len(self.SOURCE) + 1:]

        return f"{self.TARGET}-{old_id}"

    ElementType = TypeVar("ElementType", bound=ReferableElement)

    def referable_element(self, element: ElementType) -> ElementType:
        transcoded = element.__class__(self.TARGET)

        transcoded.id = self.convert_id(element.id)
        transcoded.name = element.name
        transcoded.full_name = element.full_name
        transcoded.kind = element.kind

        return transcoded

    RefType = TypeVar("RefType", bound=TypeRefBase)

    def type_ref_base(self, type_ref: RefType) -> RefType:
        transcoded = type_ref.__class__(self.TARGET)

        transcoded.id = self.convert_id(type_ref.id)
        transcoded.name = type_ref.name
        transcoded.namespace = type_ref.namespace

        return transcoded
