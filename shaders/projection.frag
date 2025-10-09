#version 330
precision highp float;

uniform sampler2D Texture0; // velocity
uniform sampler2D Texture1; // pressure
uniform vec2 resolution;

in vec2 uv;
out vec4 fragColor;

vec2 texel() { return 1.0 / resolution; }

void main() {
    vec2 px = texel();
    float pL = texture(Texture1, uv - vec2(px.x, 0)).x;
    float pR = texture(Texture1, uv + vec2(px.x, 0)).x;
    float pB = texture(Texture1, uv - vec2(0, px.y)).x;
    float pT = texture(Texture1, uv + vec2(0, px.y)).x;

    vec2 vel = texture(Texture0, uv).xy - 0.5 * vec2(pR - pL, pT - pB);
    fragColor = vec4(vel, 0, 1);
}
