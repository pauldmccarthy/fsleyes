/*
 * This file provides functions which generate random numbers. The built-in
 * GLSL noise functions are slow!.
 */

/*
 * The best reference I found for this technique is:
 *
 * https://stackoverflow.com/questions/12964279/whats-the-origin-of-this-glsl-rand-one-liner
 *
 * Returns a pseudorandom number between 0 and 1, based on e.g.
 * the screen coordinates of the current fragment.
 */

float rand(float x, float y) {
    return fract(sin(x * 12.9898 + y * 78.233) * 43758.5453);
}
