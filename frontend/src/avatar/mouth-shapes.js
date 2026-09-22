// Quatro formas de boca no mesmo estilo blocado/8-bit do avatar.svg
// atual, na escala e posição do buraco original (x 249-320, y ~370-398).
// "flat" é EXATAMENTE o recorte original extraído do path; smile/frown/
// open são variações novas, mesma família de pixel reto (sem curva).
export const MOUTH_SHAPES = {
  flat: "M 249 375 L 251 374 L 311 374 L 312 375 L 319 375 L 320 376 L 320 392 L 319 393 L 249 393 Z",
  smile:
    "M 249 378 L 253 372 L 300 370 L 313 372 L 319 375 L 320 378 L 320 392 L 316 397 L 253 397 L 249 392 Z",
  frown:
    "M 249 380 L 251 384 L 280 388 L 311 384 L 316 380 L 319 378 L 320 380 L 320 388 L 316 391 L 249 391 Z",
  open: "M 249 372 L 251 371 L 319 371 L 320 373 L 320 396 L 319 398 L 251 398 L 249 396 Z",
};
