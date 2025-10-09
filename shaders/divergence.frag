#version 330
precision highp float;

uniform sampler2D Texture0; // velocity
uniform vec2 resolution;

in vec2 uv;
out vec4 fragColor;

vec2 texel() { return 1.0 / resolution; }

void main() {
    vec2 px = texel();
    vec2 vL = texture(Texture0, uv - vec2(px.x, 0)).xy;
    vec2 vR = texture(Texture0, uv + vec2(px.x, 0)).xy;
    vec2 vB = texture(Texture0, uv - vec2(0, px.y)).xy;
    vec2 vT = texture(Texture0, uv + vec2(0, px.y)).xy;
    float div = 0.5 * ((vR.x - vL.x) + (vT.y - vB.y));
    fragColor = vec4(div, 0, 0, 1);
}
