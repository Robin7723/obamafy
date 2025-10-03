#version 330

in vec3 in_position;
out vec2 uv;

void main() {
    uv = in_position.xy * 0.5 + 0.5;
    gl_Position = vec4(in_position.xy, 0.0, 1.0);
}