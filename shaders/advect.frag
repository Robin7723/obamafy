// ./shaders/advect.frag
#version 330
precision highp float;

uniform sampler2D Texture0; // field to advect (dye or velocity)
uniform sampler2D Texture1; // velocity
uniform vec2 resolution;
uniform float dt;
uniform float dissipation;
uniform int is_dye;

in vec2 uv;
out vec4 fragColor;

vec2 texel() { return 1.0 / resolution; }

void main() {
    // --- RK2 Advection Step ---
    // 1. Get the velocity at the current point.
    vec2 v1 = texture(Texture1, uv).xy;

    // 2. Find the midpoint in time and space by stepping back half a timestep.
    vec2 mid_coord = uv - 0.5 * dt * v1 * texel();

    // 3. Get the velocity at that midpoint. This is a more accurate estimate for the whole step.
    vec2 v2 = texture(Texture1, mid_coord).xy;

    // 4. Use the midpoint velocity to advect from the original position.
    vec2 final_coord = uv - dt * v2 * texel();
    
    // --- Sample and apply dissipation ---
    vec4 src = texture(Texture0, final_coord);

    if (is_dye == 0) {
        // For velocity, just dissipate
        fragColor = src * dissipation;
    } else {
        // For dye, preserve alpha and clamp
        fragColor.rgb = src.rgb * dissipation;
        fragColor.a = 1.0;
        fragColor.rgb = clamp(fragColor.rgb, 0.0, 1.0);
    }
}