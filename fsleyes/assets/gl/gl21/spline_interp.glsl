/*--------------------------------------------------------------------------*\
Copyright (c) 2008-2009, Danny Ruijters. All rights reserved.
http://www.dannyruijters.nl/cubicinterpolation/
This file is part of CUDA Cubic B-Spline Interpolation (CI).

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
*  Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer.
*  Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in the
   documentation and/or other materials provided with the distribution.
*  Neither the name of the copyright holders nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.

The views and conclusions contained in the software and documentation are
those of the authors and should not be interpreted as representing official
policies, either expressed or implied.

When using this code in a scientific project, please cite one or all of the
following papers:
*  Daniel Ruijters and Philippe Thévenaz,
   GPU Prefilter for Accurate Cubic B-Spline Interpolation,
   The Computer Journal, vol. 55, no. 1, pp. 15-20, January 2012.
   http://dannyruijters.nl/docs/cudaPrefilter3.pdf
*  Daniel Ruijters, Bart M. ter Haar Romeny, and Paul Suetens,
   Efficient GPU-Based Texture Interpolation using Uniform B-Splines,
   Journal of Graphics Tools, vol. 13, no. 4, pp. 61-69, 2008.
\*--------------------------------------------------------------------------*/


// Tricubic interpolated texture lookup, using unnormalized coordinates.
// Fast implementation, using 8 trilinear lookups.
// @param tex        3D texture
// @param coord      normalized 3D texture coordinate
// @param nrOfVoxels Texture size
// @param comp       Texture component (0 == r, 1 == g, 2 == b, 3 == a)

float spline_interp(sampler3D tex, vec3 coord, vec3 nrOfVoxels, int comp) {

  // shift the coordinate from [0,1] to [-0.5, nrOfVoxels-0.5]
	vec3 coord_grid = coord * nrOfVoxels - 0.5;
	vec3 index = floor(coord_grid);
	vec3 fraction = coord_grid - index;
	vec3 one_frac = 1.0 - fraction;

	vec3 w0 = 1.0/6.0 * one_frac*one_frac*one_frac;
	vec3 w1 = 2.0/3.0 - 0.5 * fraction*fraction*(2.0-fraction);
	vec3 w2 = 2.0/3.0 - 0.5 * one_frac*one_frac*(2.0-one_frac);
	vec3 w3 = 1.0/6.0 * fraction*fraction*fraction;

	vec3 g0 = w0 + w1;
	vec3 g1 = w2 + w3;
	vec3 mult = 1.0 / nrOfVoxels;
	vec3 h0 = mult * ((w1 / g0) - 0.5 + index);  //h0 = w1/g0 - 1, move from [-0.5, nrOfVoxels-0.5] to [0,1]
	vec3 h1 = mult * ((w3 / g1) + 1.5 + index);  //h1 = w3/g1 + 1, move from [-0.5, nrOfVoxels-0.5] to [0,1]

   // fetch the eight linear interpolations
   // weighting and fetching is interleaved for performance and stability reasons
	float tex000 = texture3D(tex, h0)[comp];
	float tex100 = texture3D(tex, vec3(h1.x, h0.y, h0.z))[comp];
	tex000 = mix(tex100, tex000, g0.x);  //weigh along the x-direction
	float tex010 = texture3D(tex, vec3(h0.x, h1.y, h0.z))[comp];
	float tex110 = texture3D(tex, vec3(h1.x, h1.y, h0.z))[comp];
	tex010 = mix(tex110, tex010, g0.x);  //weigh along the x-direction
	tex000 = mix(tex010, tex000, g0.y);  //weigh along the y-direction
	float tex001 = texture3D(tex, vec3(h0.x, h0.y, h1.z))[comp];
	float tex101 = texture3D(tex, vec3(h1.x, h0.y, h1.z))[comp];
	tex001 = mix(tex101, tex001, g0.x);  //weigh along the x-direction
	float tex011 = texture3D(tex, vec3(h0.x, h1.y, h1.z))[comp];
	float tex111 = texture3D(tex, h1)[comp];
	tex011 = mix(tex111, tex011, g0.x);  //weigh along the x-direction
	tex001 = mix(tex011, tex001, g0.y);  //weigh along the y-direction

	return mix(tex001, tex000, g0.z);  //weigh along the z-direction
}


float spline_interp(sampler2D tex, vec2 coord, vec2 nrOfVoxels, int comp) {
  // shift the coordinate from [0,1] to [-0.5, nrOfPixels-0.5]
  //vec2 nrOfPixels = vec2(textureSize2D(uSampler, 0));
  vec2 coord_grid = coord * nrOfVoxels - 0.5;
  vec2 index = floor(coord_grid);
  vec2 fraction = coord_grid - index;
  vec2 one_frac = 1.0 - fraction;

  vec2 w0 = 1.0/6.0 * one_frac*one_frac*one_frac;
  vec2 w1 = 2.0/3.0 - 0.5 * fraction*fraction*(2.0-fraction);
  vec2 w2 = 2.0/3.0 - 0.5 * one_frac*one_frac*(2.0-one_frac);
  vec2 w3 = 1.0/6.0 * fraction*fraction*fraction;

  vec2 g0 = w0 + w1;
  vec2 g1 = w2 + w3;
  vec2 mult = 1.0 / nrOfVoxels;
  //h0 = w1/g0 - 1, move from [-0.5, nrOfVoxels-0.5] to [0,1]
  vec2 h0 = mult * ((w1 / g0) - 0.5 + index);
  //h1 = w3/g1 + 1, move from [-0.5, nrOfVoxels-0.5] to [0,1]
  vec2 h1 = mult * ((w3 / g1) + 1.5 + index);

  // fetch the four linear interpolations
  float tex00 = texture2D(tex, h0)[comp];
  float tex10 = texture2D(tex, vec2(h1.x, h0.y))[comp];
  tex00 = mix(tex10, tex00, g0.x);  //weigh along the x-direction
  float tex01 = texture2D(tex, vec2(h0.x, h1.y))[comp];
  float  tex11 = texture2D(tex, h1)[comp];
  tex01 = mix(tex11, tex01, g0.x);  //weigh along the x-direction
  return mix(tex01, tex00, g0.y);  //weigh along the y-direction
}
