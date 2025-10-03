#version 330
precision highp float;

uniform sampler2D Texture0; // dye
uniform sampler2D Texture1; // velocity
uniform sampler2D Texture2; // pressure
uniform sampler2D Texture3; // divergence
uniform sampler2D Texture4; // target
uniform vec2 resolution;
uniform int view_mode;

in vec2 uv;
out vec4 fragColor;

void main() {
    if (view_mode == 1) {
        // Final: just show the dye (it will converge to target via forces)
        vec3 dye = texture(Texture0, uv).rgb;
        // Apply gamma correction for display
        fragColor = vec4(pow(dye, vec3(1.0/2.2)), 1.0);
    } else if (view_mode == 2) {
        vec2 v = texture(Texture1, uv).xy * 0.5 + 0.5;
        fragColor = vec4(v, 0.2, 1.0);
    } else if (view_mode == 3) {
        float p = texture(Texture2, uv).x;
        p = 0.5 + 0.5 * tanh(p * 2.0);
        fragColor = vec4(p, p, p, 1.0);
    } else if (view_mode == 4) {
        float d = texture(Texture3, uv).x;
        d = 0.5 + 0.5 * tanh(d * 4.0);
        fragColor = vec4(d, 0.2, 1.0 - d, 1.0);
    } else if (view_mode == 5) {
        // Debug: show target image
        vec3 tgt = texture(Texture4, uv).rgb;
        fragColor = vec4(pow(tgt, vec3(1.0/2.2)), 1.0);
    }
}