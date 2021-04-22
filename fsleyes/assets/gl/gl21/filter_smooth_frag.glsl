/*
 * Filter fragment shader which performs basic smoothing on a texture.
 *
 * Each fragment is replaced with a weighted average of the fragment and its
 * neighbours, with the weight for each neighbouring fragment linearly
 * proportional to its distance from the target fragment.
 */
#version 120


/* Texture to be smoothed. */
uniform sampler2D texture;

/* Distance between adjacent fragments, in texture coordinates. */
uniform vec2 offsets;

/*
 * Size of the smoothing kernel - a square kernel of size (kernSize, kernSize)
 * will be used. If kernSize is even, it will be forced to be odd.
 */
uniform int kernSize;

/* Coordinates of current fragment. */
varying vec2 fragTexCoord;


void main(void) {

  float dist;
  vec2  point;
  int   nsteps;
  int   midstep;

  vec2  off;
  vec4  val;
  float maxdist;
  float cumdist = 0;
  vec4  rgba    = vec4(0);

  // force kernel size to be odd
  if (mod(kernSize, 2) == 0)
    nsteps = kernSize + 1;
  else
    nsteps = kernSize;

  midstep = nsteps / 2;

  // distance from the target fragment
  // to the farthest fragments (the
  // corners of the kernel). Used for
  // normalisation.
  if (midstep == 0)
    maxdist = 1;
  else
    maxdist = distance(vec2(0, 0), vec2(midstep, midstep));

  for (int xi = 0; xi < nsteps; xi++) {
    for (int yi = 0; yi < nsteps; yi++) {

      off   = vec2(xi - midstep, yi - midstep);
      point = fragTexCoord + off * offsets;
      val   = texture2D(texture, point);

      if (val.a == 0) {
        continue;
      }

      // Invert the distance so closer fragments
      // weigh more. Accumulate the total distance
      // so we can normalise at the end (with the
      // effect that all of the kernel weights will
      // add to 1).
      dist     = maxdist - distance(vec2(0, 0), off);
      cumdist += dist;
      rgba    += val * dist;
    }
  }

  gl_FragColor = rgba / cumdist;
}
