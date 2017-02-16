/*
 * Fragment shader used for drawing GLMesh outlines.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com> 
 */
#version 120

/* Colour map to use */
uniform sampler1D cmap;

/* Colour map to use for negative values, if useNegCmap is true */
uniform sampler1D negCmap;

/* Transformation from data values to colour map texture coordinates */
uniform mat4      cmapXform;

/* Use negCmap for negative values */
uniform bool      useNegCmap;

/* Invert the clipping range */
uniform bool      invertClip;

/* Clip values <= this value */
uniform float     clipLow;

/* Clip values >= this value  */
uniform float     clipHigh;

/* Vertex data value */
varying float     fragVertexData;


void main(void) {

  float vertexData;
  float texCoord;
  float clipValue;
  bool  negative;
  
  negative = useNegCmap && fragVertexData < 0;

  if (negative) vertexData = -fragVertexData;
  else          vertexData =  fragVertexData;

  if ((!invertClip && (vertexData <= clipLow || vertexData >= clipHigh)) ||
      ( invertClip && (vertexData >= clipLow && vertexData <= clipHigh))) {
    discard;
  }
    
  texCoord = (cmapXform * vec4(vertexData, 0, 0, 1)).x;

  if (negative) gl_FragColor = texture1D(negCmap, texCoord);
  else          gl_FragColor = texture1D(cmap,    texCoord);
}
