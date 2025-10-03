// ./shaders/apply_forces.frag
#version 330
precision highp float;

// UNIFORMS
uniform sampler2D Texture0; // velocity in
uniform sampler2D Texture1; // dye (current)
uniform sampler2D Texture2; // target image
uniform sampler2D Texture3; // static noise texture

uniform vec2 resolution;
uniform float dt;
uniform float time;

uniform float convergence_force;
uniform float settling_strength;
uniform float turbulence_strength;
uniform float vorticity_eps;

uniform int has_mouse;
uniform vec2 mouse_uv;
uniform vec2 mouse_vel;
uniform float mouse_radius;

in vec2 uv;
out vec4 fragColor;

vec2 texel() { return 1.0 / resolution; }

vec2 get_vorticity_force(vec2 p, vec2 px) {
    // Sample velocity at neighboring cells
    vec2 vl = texture(Texture0, p - vec2(px.x, 0)).xy;
    vec2 vr = texture(Texture0, p + vec2(px.x, 0)).xy;
    vec2 vb = texture(Texture0, p - vec2(0, px.y)).xy;
    vec2 vt = texture(Texture0, p + vec2(0, px.y)).xy;

    // Compute curl (vorticity) at current cell
    float curl = 0.5 * ((vr.y - vl.y) - (vt.x - vb.x));

    // To find the gradient of the curl, we need the curl at neighboring cells.
    // This is expensive as it requires many more texture lookups.
    // A simpler (but effective) approximation is to find the gradient of the *magnitude* of curl.
    float curlL = 0.5 * ((texture(Texture0, p).y - texture(Texture0, p - 2.0*vec2(px.x,0)).y) - (texture(Texture0, p - vec2(px.x, -px.y)).x - texture(Texture0, p - vec2(px.x, px.y)).x));
    float curlR = 0.5 * ((texture(Texture0, p + 2.0*vec2(px.x,0)).y - texture(Texture0, p).y) - (texture(Texture0, p + vec2(px.x, -px.y)).x - texture(Texture0, p + vec2(px.x, px.y)).x));
    float curlB = 0.5 * ((texture(Texture0, p + vec2(0, -px.y)).y - texture(Texture0, p - vec2(0, px.y)).y) - (texture(Texture0, p).x - texture(Texture0, p - 2.0*vec2(0,px.y)).x));
    float curlT = 0.5 * ((texture(Texture0, p + vec2(0, px.y)).y - texture(Texture0, p - vec2(0, px.y)).y) - (texture(Texture0, p + 2.0*vec2(0,px.y)).x - texture(Texture0, p).x));
    
    vec2 grad = 0.5 * vec2(abs(curlR) - abs(curlL), abs(curlT) - abs(curlB));
    
    // Normalize and compute vorticity confinement force
    vec2 N = grad / (length(grad) + 1e-5);
    vec2 force = vorticity_eps * vec2(N.y, -N.x) * curl;
    return force;
}


// Function to get curl of the noise field, creating swirly turbulence
// By sampling from different mipmap levels, we get noise at different scales
vec2 get_turbulence(vec2 p) {
    vec2 px = texel();
    float s = 0.5; // Scale for sampling
    
    // Sample noise at different scales (mip levels) and combine their curls
    float l1 = textureLod(Texture3, p - vec2(px.x, 0.0) * s, 1.0).y;
    float r1 = textureLod(Texture3, p + vec2(px.x, 0.0) * s, 1.0).y;
    float b1 = textureLod(Texture3, p - vec2(0.0, px.y) * s, 1.0).x;
    float t1 = textureLod(Texture3, p + vec2(0.0, px.y) * s, 1.0).x;
    vec2 curl1 = vec2(t1 - b1, l1 - r1);

    float l2 = textureLod(Texture3, p - vec2(px.x, 0.0) * s, 3.0).y;
    float r2 = textureLod(Texture3, p + vec2(px.x, 0.0) * s, 3.0).y;
    float b2 = textureLod(Texture3, p - vec2(0.0, px.y) * s, 3.0).x;
    float t2 = textureLod(Texture3, p + vec2(0.0, px.y) * s, 3.0).x;
    vec2 curl2 = vec2(t2 - b2, l2 - r2);

    float l3 = textureLod(Texture3, p - vec2(px.x, 0.0) * s, 5.0).y;
    float r3 = textureLod(Texture3, p + vec2(px.x, 0.0) * s, 5.0).y;
    float b3 = textureLod(Texture3, p - vec2(0.0, px.y) * s, 5.0).x;
    float t3 = textureLod(Texture3, p + vec2(0.0, px.y) * s, 5.0).x;
    vec2 curl3 = vec2(t3 - b3, l3 - r3);

    return (curl1 * 0.7 + curl2 * 0.2 + curl3 * 0.1) * turbulence_strength;
}

float luminance(vec3 color) {
    return dot(color, vec3(0.299, 0.587, 0.114));
}

void main() {
    vec2 px = texel();
    vec2 current_vel = texture(Texture0, uv).xy;

    // --- 1. VORTICITY CONFINEMENT FORCE ---
    vec2 vorticity_force_vec = get_vorticity_force(uv, px);

    // --- 2. CONVERGENCE FORCE ---
    float target_lum = luminance(texture(Texture2, uv).rgb);

    float err_L = abs(target_lum - luminance(texture(Texture1, uv - vec2(px.x, 0)).rgb));
    float err_R = abs(target_lum - luminance(texture(Texture1, uv + vec2(px.x, 0)).rgb));
    float err_B = abs(target_lum - luminance(texture(Texture1, uv - vec2(0, px.y)).rgb));
    float err_T = abs(target_lum - luminance(texture(Texture1, uv + vec2(0, px.y)).rgb));

    vec2 grad_error = vec2(err_R - err_L, err_T - err_B);
    vec2 convergence_force_vec = grad_error * convergence_force * 5.0;

    // vec3 current_dye = texture(Texture1, uv).rgb;
    // vec3 target_dye = texture(Texture2, uv).rgb;
    // float err_L = length(target_dye - texture(Texture1, uv - vec2(px.x, 0)).rgb);
    // float err_R = length(target_dye - texture(Texture1, uv + vec2(px.x, 0)).rgb);
    // float err_B = length(target_dye - texture(Texture1, uv - vec2(0, px.y)).rgb);
    // float err_T = length(target_dye - texture(Texture1, uv + vec2(0, px.y)).rgb);
    // vec2 grad_error = vec2(err_R - err_L, err_T - err_B);
    // vec2 convergence_force_vec = grad_error * convergence_force * 5.0;

    // --- 3. DYNAMIC DAMPING (SETTLING) FORCE ---
    vec3 current_dye = texture(Texture1, uv).rgb;
    vec3 target_dye = texture(Texture2, uv).rgb;
    float error_mag = abs(luminance(target_dye) - luminance(current_dye));
    float damping_factor = pow(1.0 - smoothstep(0.0, 0.4, error_mag), 2.0);
    vec2 damping_force = -current_vel * settling_strength * damping_factor;

    // float error_mag = length(target_dye - current_dye);
    // float damping_factor = pow(1.0 - smoothstep(0.0, 0.4, error_mag), 2.0);
    // vec2 damping_force = -current_vel * settling_strength * damping_factor;

    // --- 4. TURBULENCE FORCE ---
    vec2 turbulence_force_vec = get_turbulence(uv + time * 0.01);

    // --- 5. MOUSE FORCE ---
    vec2 mouse_impulse_vec = vec2(0);
    if (has_mouse == 1) {
        float d = distance(uv, mouse_uv);
        float falloff = smoothstep(mouse_radius, 0.0, d);
        vec2 dir = uv - mouse_uv;
        vec2 swirl_dir = vec2(-dir.y, dir.x);
        vec2 push_impulse = mouse_vel * 10000.0 * falloff;
        vec2 swirl_impulse = normalize(swirl_dir + 1e-5) * 5.0 * falloff;
        mouse_impulse_vec = push_impulse + swirl_impulse;
        damping_force = vec2(0);
        convergence_force_vec = vec2(0);
    }

    // --- COMBINE ALL FORCES ---
    vec2 continuous_forces = vorticity_force_vec + convergence_force_vec + damping_force + turbulence_force_vec;
    vec2 new_vel = current_vel + dt * continuous_forces;
    new_vel += mouse_impulse_vec;

    fragColor = vec4(new_vel, 0, 1);
}