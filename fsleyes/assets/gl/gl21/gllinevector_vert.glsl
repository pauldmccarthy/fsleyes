/*
 * OpenGL vertex shader used for rendering GLVector instances in
 * line mode.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

/*
 * Vector image containing XYZ vector data.
 */
uniform sampler3D vectorTexture;

/*
 * Transformations between voxel and
 * display coordinate systems, incorporating
 * the model view projection transform.
 */
uniform mat4 voxToDisplayMat;

/*
 * Camera direction vector, and a rotation matrix
 * which rotates 90 degrees about that vector.
 * Used to position vertices on the rectangle
 * that is used to represent each line vector.
 */
uniform vec3 camera;
uniform mat3 cameraRotation;

/*
 * Matrices which transform from vector
 * texture coordinates to colour/clip/
 * modulate image texture coordinates.
 */
uniform mat4 colourCoordXform;
uniform mat4 clipCoordXform;
uniform mat4 modCoordXform;

/*
 * Transformation matrix which transforms the
 * vector texture data to its original data range.
 */
uniform mat4 voxValXform;

/*
 * Shape of the image texture.
 */
uniform vec3 imageShape;

/*
 * Dimensions of one voxel in the image texture.
 */
uniform vec3 imageDims;

/*
 * If true, the vectors are
 * inverted about the x axis.
 */
uniform bool xFlip;

/*
 * Line vectors are interpreted as directed - each
 * line begins in the centre of its voxel, and extends
 * outwards.
 */
uniform bool directed;

/*
 * Scale vector lengths by this amount.
 */
uniform float lengthScale;

/*
 * Draw lines this thick.
 */
uniform float lineWidth;

/*
 * The current vertex on the current line.
 */
attribute vec3 voxel;

/*
 * Vertex index - the built-in gl_VertexID
 * variable is not available in GLSL 120
 */
attribute float vertexID;


varying vec3 fragVoxCoord;
varying vec3 fragTexCoord;
varying vec3 fragVecTexCoord;
varying vec3 fragClipTexCoord;
varying vec3 fragModTexCoord;
varying vec4 fragColourFactor;

void main(void) {

  vec3 texCoord;
  vec3 vector;
  vec3 vertex;
  vec3 offset;
  vec3 voxCoord;

  /*
   * Normalise the voxel coordinates to [0.0, 1.0],
   * so they can be used for texture lookup. Add
   * 0.5 to the voxel coordinates first, to re-centre
   * voxel coordinates from  from [i - 0.5, i + 0.5]
   * to [i, i + 1].
   */
  voxCoord = voxel;
  texCoord = (voxCoord + 0.5) / imageShape;

  /*
   * Retrieve the vector values for this voxel
   */
  vector = texture3D(vectorTexture, texCoord).xyz;

  /*
   * Transform the vector values  from their
   * texture range of [0,1] to the original
   * data range
   */
  vector *= voxValXform[0].x;
  vector += voxValXform[3].x;

  /* Invert about the x axis if necessary */
  if (xFlip) {
    vector.x = -vector.x;
  }

  /*
   * Kill the vector if its length is 0.
   * We have to be tolerant of errors,
   * because of the transformation to/
   * from the texture data range. This
   * may end up being too tolerant.
   */
  if (length(vector) < 0.0001) {
    fragColourFactor = vec4(0, 0, 0, 0);
    return;
  }

  /*
   * Project the vector onto the viewing plane,
   * so we can figure out an offset to position
   * the rectangle corners (so the rectangle
   * corners are 90 degrees).
   */
  vertex = vector * lengthScale;
  vector = vector - (camera * dot(vector, camera));
  offset = normalize(cameraRotation * vector) * lineWidth / 2;

  /*
   * Vertices are coming in as corners of
   * the line rectangle, identified by the
   * vertesxID.  Flip/offset vertices
   * depending on which corner we are at.
   */
  if (vertexID == 0) {
    vertex = vertex - offset;
  }
  else if (vertexID == 1) {
    vertex = vertex + offset;
  }
  else if (vertexID == 2) {
    if (directed) vertex = -offset;
    else          vertex = -vertex - offset;
  }
  else if (vertexID == 3) {
    if (directed) vertex =  offset;
    else          vertex = -vertex + offset;
  }

  /*
   * Output the final vertex position - offset
   * the voxel coordinates by the vector values,
   * and transform back to display coordinates
   */
  gl_Position = voxToDisplayMat * vec4(voxCoord + vertex, 1);

  fragVoxCoord     = voxCoord;
  fragVecTexCoord  = texCoord;
  fragTexCoord     = (colourCoordXform * vec4(texCoord, 1)).xyz;
  fragClipTexCoord = (clipCoordXform   * vec4(texCoord, 1)).xyz;
  fragModTexCoord  = (modCoordXform    * vec4(texCoord, 1)).xyz;
  fragColourFactor = vec4(1, 1, 1, 1);
}
