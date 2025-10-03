#version 330
precision highp float;

uniform sampler2D Texture0; // velocity
uniform vec2 resolution;
uniform float dt;
uniform float vorticity_eps;

in vec2 uv;
out vec4 fragColor;

vec2 texel() { return 1.0 / resolution; }

void main() {
    vec2 px = texel();
    
    // Sample velocity at neighboring cells
    vec2 vl = texture(Texture0, uv - vec2(px.x, 0)).xy;
    vec2 vr = texture(Texture0, uv + vec2(px.x, 0)).xy;
    vec2 vb = texture(Texture0, uv - vec2(0, px.y)).xy;
    vec2 vt = texture(Texture0, uv + vec2(0, px.y)).xy;

    // Compute curl (vorticity) at current cell
    float curl = 0.5 * ((vr.y - vl.y) - (vt.x - vb.x));

    // Compute curl at neighboring cells for gradient calculation
    vec2 uvL = uv - vec2(px.x, 0);
    vec2 uvR = uv + vec2(px.x, 0);
    vec2 uvB = uv - vec2(0, px.y);
    vec2 uvT = uv + vec2(0, px.y);
    
    // Curl at left neighbor
    vec2 vl_l = texture(Texture0, uvL - vec2(px.x, 0)).xy;
    vec2 vl_r = texture(Texture0, uvL + vec2(px.x, 0)).xy;
    vec2 vl_b = texture(Texture0, uvL - vec2(0, px.y)).xy;
    vec2 vl_t = texture(Texture0, uvL + vec2(0, px.y)).xy;
    float curlL = 0.5 * ((vl_r.y - vl_l.y) - (vl_t.x - vl_b.x));
    
    // Curl at right neighbor
    vec2 vr_l = texture(Texture0, uvR - vec2(px.x, 0)).xy;
    vec2 vr_r = texture(Texture0, uvR + vec2(px.x, 0)).xy;
    vec2 vr_b = texture(Texture0, uvR - vec2(0, px.y)).xy;
    vec2 vr_t = texture(Texture0, uvR + vec2(0, px.y)).xy;
    float curlR = 0.5 * ((vr_r.y - vr_l.y) - (vr_t.x - vr_b.x));
    
    // Curl at bottom neighbor
    vec2 vb_l = texture(Texture0, uvB - vec2(px.x, 0)).xy;
    vec2 vb_r = texture(Texture0, uvB + vec2(px.x, 0)).xy;
    vec2 vb_b = texture(Texture0, uvB - vec2(0, px.y)).xy;
    vec2 vb_t = texture(Texture0, uvB + vec2(0, px.y)).xy;
    float curlB = 0.5 * ((vb_r.y - vb_l.y) - (vb_t.x - vb_b.x));
    
    // Curl at top neighbor
    vec2 vt_l = texture(Texture0, uvT - vec2(px.x, 0)).xy;
    vec2 vt_r = texture(Texture0, uvT + vec2(px.x, 0)).xy;
    vec2 vt_b = texture(Texture0, uvT - vec2(0, px.y)).xy;
    vec2 vt_t = texture(Texture0, uvT + vec2(0, px.y)).xy;
    float curlT = 0.5 * ((vt_r.y - vt_l.y) - (vt_t.x - vt_b.x));
    
    // Gradient of absolute curl magnitude
    vec2 grad = 0.5 * vec2(abs(curlR) - abs(curlL), abs(curlT) - abs(curlB));
    
    // Normalize and compute vorticity confinement force
    float mag = length(grad) + 1e-5;
    vec2 N = grad / mag;
    vec2 force = vorticity_eps * vec2(N.y, -N.x) * curl;

    vec2 vel = texture(Texture0, uv).xy + dt * force;
    fragColor = vec4(vel, 0, 1);
}