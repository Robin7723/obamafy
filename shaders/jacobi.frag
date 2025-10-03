
#version 330
precision highp float;

uniform sampler2D Texture0; // pressure
uniform sampler2D Texture1; // divergence
uniform vec2 resolution;

in vec2 uv;
out vec4 fragColor;

vec2 texel() { return 1.0 / resolution; }

void main() {
    vec2 px = texel();
    float div = texture(Texture1, uv).x;

    float pL = texture(Texture0, uv - vec2(px.x, 0)).x;
    float pR = texture(Texture0, uv + vec2(px.x, 0)).x;
    float pB = texture(Texture0, uv - vec2(0, px.y)).x;
    float pT = texture(Texture0, uv + vec2(0, px.y)).x;

    float p = (pL + pR + pB + pT - div) * 0.25;
    fragColor = vec4(p,0,0,1);
}
