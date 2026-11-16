# -*- coding: utf-8 -*-
"""Mały pomocnik do budowania drzew węzłów shaderów z Pythona (matematyka na gniazdach).

    W = Wezly(material.node_tree)
    x = W.math("MULTIPLY", W.sep(coord)[0], 2.0)
"""
import bpy


class Wezly:
    def __init__(self, nt):
        self.nt = nt
        self.n = 0

    def _node(self, typ, **kw):
        nd = self.nt.nodes.new(typ)
        nd.location = ((self.n % 40) * 180, -(self.n // 40) * 200)
        self.n += 1
        for k, v in kw.items():
            setattr(nd, k, v)
        return nd

    def _in(self, sock, val):
        if val is None:
            return
        if isinstance(val, bpy.types.NodeSocket):
            self.nt.links.new(val, sock)
        else:
            sock.default_value = val

    # --- skalary
    def math(self, op, a, b=None, c=None, clamp=False):
        nd = self._node("ShaderNodeMath", operation=op, use_clamp=clamp)
        self._in(nd.inputs[0], a)
        if b is not None:
            self._in(nd.inputs[1], b)
        if c is not None:
            self._in(nd.inputs[2], c)
        return nd.outputs[0]

    def add(self, a, b): return self.math("ADD", a, b)
    def sub(self, a, b): return self.math("SUBTRACT", a, b)
    def mul(self, a, b): return self.math("MULTIPLY", a, b)
    def div(self, a, b): return self.math("DIVIDE", a, b)
    def mn(self, a, b): return self.math("MINIMUM", a, b)
    def mx(self, a, b): return self.math("MAXIMUM", a, b)

    def wartosc(self, v, nazwa=None):
        nd = self._node("ShaderNodeValue")
        nd.outputs[0].default_value = v
        if nazwa:
            nd.name = nazwa
            nd.label = nazwa
        return nd.outputs[0]

    def smooth(self, e0, e1, x):
        """smoothstep(e0, e1, x) przez Map Range (SMOOTHSTEP)."""
        nd = self._node("ShaderNodeMapRange", interpolation_type="SMOOTHSTEP", clamp=True)
        self._in(nd.inputs["Value"], x)
        self._in(nd.inputs["From Min"], e0)
        self._in(nd.inputs["From Max"], e1)
        nd.inputs["To Min"].default_value = 0.0
        nd.inputs["To Max"].default_value = 1.0
        return nd.outputs["Result"]

    def linia(self, odl, polgrubosc, miekkosc):
        """1 w pobliżu odl=0 (|odl| < polgrubosc), miękka krawędź."""
        a = self.math("ABSOLUTE", odl)
        return self.sub(1.0, self.smooth(polgrubosc - miekkosc, polgrubosc + miekkosc, a))

    # --- wektory
    def vmath(self, op, a, b=None, scale=None):
        nd = self._node("ShaderNodeVectorMath", operation=op)
        self._in(nd.inputs[0], a)
        if b is not None:
            self._in(nd.inputs[1], b)
        if scale is not None:
            self._in(nd.inputs["Scale"], scale)
        if op in ("DOT_PRODUCT", "LENGTH", "DISTANCE"):
            return nd.outputs["Value"]
        return nd.outputs["Vector"]

    def vec(self, x, y=None, z=None):
        nd = self._node("ShaderNodeCombineXYZ")
        if y is None and isinstance(x, (tuple, list)):
            x, y, z = x
        self._in(nd.inputs[0], x)
        self._in(nd.inputs[1], y)
        self._in(nd.inputs[2], z)
        return nd.outputs[0]

    def sep(self, v):
        nd = self._node("ShaderNodeSeparateXYZ")
        self._in(nd.inputs[0], v)
        return nd.outputs[0], nd.outputs[1], nd.outputs[2]

    def scale(self, v, s): return self.vmath("SCALE", v, scale=s)
    def vadd(self, a, b): return self.vmath("ADD", a, b)
    def dot(self, a, b): return self.vmath("DOT_PRODUCT", a, b)
    def norm(self, v): return self.vmath("NORMALIZE", v)

    def obrot(self, v, os_, kat, srodek=(0, 0, 0)):
        nd = self._node("ShaderNodeVectorRotate", rotation_type="AXIS_ANGLE")
        self._in(nd.inputs["Vector"], v)
        self._in(nd.inputs["Center"], srodek)
        self._in(nd.inputs["Axis"], os_)
        self._in(nd.inputs["Angle"], kat)
        return nd.outputs[0]

    # --- kolory
    def rgb(self, c):
        nd = self._node("ShaderNodeRGB")
        nd.outputs[0].default_value = c
        return nd.outputs[0]

    def mix(self, fac, a, b):
        nd = self._node("ShaderNodeMix", data_type="RGBA", blend_type="MIX", clamp_factor=True)
        self._in(nd.inputs["Factor"], fac)
        self._in(nd.inputs[6], a)
        self._in(nd.inputs[7], b)
        return nd.outputs[2]

    def mixv(self, fac, a, b):
        nd = self._node("ShaderNodeMix", data_type="VECTOR", clamp_factor=True)
        self._in(nd.inputs["Factor"], fac)
        self._in(nd.inputs[4], a)
        self._in(nd.inputs[5], b)
        return nd.outputs[1]

    def obraz(self, image, wektor, interp="Linear", ext="REPEAT"):
        nd = self._node("ShaderNodeTexImage", interpolation=interp, extension=ext)
        nd.image = image
        self._in(nd.inputs["Vector"], wektor)
        return nd.outputs["Color"], nd.outputs["Alpha"]

    def srodowisko(self, image, kierunek, interp="Linear"):
        nd = self._node("ShaderNodeTexEnvironment", interpolation=interp)
        nd.image = image
        self._in(nd.inputs["Vector"], kierunek)
        return nd.outputs["Color"]

    def coord(self, typ="Object"):
        nd = self._node("ShaderNodeTexCoord")
        return nd.outputs[typ]

    def geometria(self, wyj="Normal"):
        nd = self._node("ShaderNodeNewGeometry")
        return nd.outputs[wyj]

    def emisja_wyjscie(self, kolor, alfa=None):
        out = self._node("ShaderNodeOutputMaterial")
        em = self._node("ShaderNodeEmission")
        self._in(em.inputs["Color"], kolor)
        em.inputs["Strength"].default_value = 1.0
        if alfa is None:
            self.nt.links.new(em.outputs[0], out.inputs["Surface"])
        else:
            tr = self._node("ShaderNodeBsdfTransparent")
            mx = self._node("ShaderNodeMixShader")
            self._in(mx.inputs[0], alfa)
            self.nt.links.new(tr.outputs[0], mx.inputs[1])
            self.nt.links.new(em.outputs[0], mx.inputs[2])
            self.nt.links.new(mx.outputs[0], out.inputs["Surface"])
        return out


def animuj_wartosc(nt, nazwa, klucze, interp="BEZIER"):
    """Klucze (klatka, wartość) dla węzła Value o danej nazwie w drzewie nt (materiału)."""
    nd = nt.nodes[nazwa]
    for f, v in klucze:
        nd.outputs[0].default_value = v
        nd.outputs[0].keyframe_insert("default_value", frame=f)
    import globus as G
    G.wygladz(nt, interp)
