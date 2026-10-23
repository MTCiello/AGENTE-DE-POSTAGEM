import { type OfficeLayout, TILE_SIZE, TileType } from '../office/types.js';

/**
 * Deslocamento da câmera (pixels do canvas) que põe o escritório desenhado no meio da tela.
 *
 * Com deslocamento zero o centro da grade fica no centro da tela; mas a grade pode ter sobra vazia (VOID)
 * de um lado, e as paredes de cima sobem um quadrado acima da sua linha. Então centraliza pelo que
 * aparece de fato: o retângulo dos quadrados não vazios, com as paredes um quadrado mais altas.
 */
export function panCentralizado(layout: OfficeLayout, zoom: number): { x: number; y: number } {
  let c0 = Infinity;
  let c1 = -Infinity;
  let r0 = Infinity;
  let r1 = -Infinity;
  for (let r = 0; r < layout.rows; r++) {
    for (let c = 0; c < layout.cols; c++) {
      if (layout.tiles[r * layout.cols + c] === TileType.VOID) continue;
      c0 = Math.min(c0, c);
      c1 = Math.max(c1, c);
      r0 = Math.min(r0, r);
      r1 = Math.max(r1, r);
    }
  }
  if (c1 < 0) return { x: 0, y: 0 };
  const topoTemParede = layout.tiles.slice(r0 * layout.cols, (r0 + 1) * layout.cols).includes(TileType.WALL);
  const topo = topoTemParede ? r0 - 1 : r0;
  const centroX = (c0 + c1 + 1) / 2;
  const centroY = (topo + r1 + 1) / 2;
  return {
    x: Math.round((layout.cols / 2 - centroX) * TILE_SIZE * zoom),
    y: Math.round((layout.rows / 2 - centroY) * TILE_SIZE * zoom),
  };
}
