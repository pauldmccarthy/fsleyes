/*
 * OpenGL vertex shader used for rendering GLVector instances in
 * line mode.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

#pragma include spline_interp.glsl

/*
 * Vector image containing XYZ vector data.
 */
uniform sampler3D imageTexture;


uniform mat4 displayToVoxMat;
uniform mat4 voxToDisplayMat;


/*
 * Transformation matrix which transforms the
 * vector texture data to its original data range.
 */
uniform mat4 voxValXform;


/*
 * Shape of the image texture.
 */
uniform vec3 imageShape;


uniform bool directed;

/*
 * Dimensions of one voxel in the image texture.
 */
uniform vec3 imageDims;


attribute vec3 vertex;

/*
 * Vertex index - the built-in gl_VertexID
 * variable is not available in GLSL 120
 */
attribute float vertexID;


varying vec3 fragVoxCoord;
varying vec3 fragTexCoord;


void main(void) {

  vec3 texCoord;
  vec3 vector;
  vec3 voxCoord;
  vec3 vertVoxCoord;

  /*
   * The vertVoxCoord vector contains the floating
   * point voxel coordinates which correspond to the
   * display coordinates of the current vertex.
   */
  vertVoxCoord = (displayToVoxMat * vec4(vertex, 1)).xyz;

  /*
   * The voxCoord vector contains the exact integer
   * voxel coordinates - we cannot interpolate vector
   * directions.
   *
   * There is no round function in GLSL 1.2, so we use
   * floor(x + 0.5).
   */  
  voxCoord = floor(vertVoxCoord + 0.5);
  
  /*
   * Normalise the voxel coordinates to [0.0, 1.0],
   * so they can be used for texture lookup. Add
   * 0.5 to the voxel coordinates first, to re-centre
   * voxel coordinates from  from [i - 0.5, i + 0.5]
   * to [i, i + 1].
   */
  texCoord = (voxCoord + 0.5) / imageShape;

  /*
   * Retrieve the vector values for this voxel
   */
  vector = texture3D(imageTexture, texCoord).xyz;

  /*
   * Transform the vector values  from their
   * texture range of [0,1] to the original
   * data range
   */
  vector *= voxValXform[0].x;
  vector += voxValXform[3].x;

  // Scale the vector so it has length 0.5 
  vector /= 2 * length(vector);

  /*
   * Scale the vector by the minimum voxel length,
   * so it is a unit vector within real world space 
   */
  vector /= imageDims / min(imageDims.x, min(imageDims.y, imageDims.z));

  /*
   * Vertices are coming in as line pairs - flip
   * every second vertex about the origin
   */
  if (mod(vertexID, 2) == 1) {
    if (directed) vector = vec3(0, 0, 0);
    else          vector = -vector;
  }

  /*
   * Output the final vertex position - offset
   * the voxel coordinates by the vector values,
   * and transform back to display coordinates
   */
  gl_Position = gl_ModelViewProjectionMatrix *
                voxToDisplayMat              *
                vec4(vertVoxCoord + vector, 1);

  fragVoxCoord = voxCoord;
  fragTexCoord = texCoord;
}
