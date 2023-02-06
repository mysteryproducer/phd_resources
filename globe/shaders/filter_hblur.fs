#include std_head_fs.inc

varying vec2 texcoordout;
const float texConst=1.0/512.0;

void main(void) {
  vec4 texc = vec4(0.0, 0.0, 0.0, 1.0); // we don't save the alpha value of the rendering so set this here to 1.0
//  vec2 fcoord = vec2(0.0, 0.0);
  // because the for loops cant run over variable size we have to use a 5 x 5 grid and vary the spread that is sampled
  // obviously this will lead to grainy effects with large amounts of blur
  // unif[14][0] the focus distance
  // unif[14][1] the depth of focus (how narrow or broad a band in focus)
  // unif[14][2] the amount of blurring to apply
  // unif[16][0] distance at which objects stop being visible
  float depth = texture2D(tex1, texcoordout)[0]; //TODO correct dist formula
  float spread = clamp(unif[14][2] * abs((depth - unif[14][0]) / unif[14][1]), 0.0, unif[14][2]);
  float blurSize=spread*texConst;
  
  texc+=texture2D(tex0, vec2(texcoordout.x - 4.0*blurSize, texcoordout.y)) * 0.05;
  texc+=texture2D(tex0, vec2(texcoordout.x - 3.0*blurSize, texcoordout.y)) * 0.09;
  texc+=texture2D(tex0, vec2(texcoordout.x - 2.0*blurSize, texcoordout.y)) * 0.12;
  texc+=texture2D(tex0, vec2(texcoordout.x - blurSize, texcoordout.y)) * 0.15;
  texc+=texture2D(tex0, vec2(texcoordout.x, texcoordout.y)) * 0.16;
  texc+=texture2D(tex0, vec2(texcoordout.x - blurSize, texcoordout.y)) * 0.15;
  texc+=texture2D(tex0, vec2(texcoordout.x - 2.0*blurSize, texcoordout.y)) * 0.12;
  texc+=texture2D(tex0, vec2(texcoordout.x - 3.0*blurSize, texcoordout.y)) * 0.09;
  texc+=texture2D(tex0, vec2(texcoordout.x - 4.0*blurSize, texcoordout.y)) * 0.05;
  gl_FragColor=texc;

  //gl_FragColor = vec4(1.0,0.4,0.1,1.0);
}