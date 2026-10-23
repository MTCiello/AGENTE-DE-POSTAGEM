/**
 * A sala do Gerente é fechada (porta de carvalho): parado, o Gerente passeia só por ela, para ser fácil de achar, e os
 * outros agentes não entram nela nem nos Arquivos (que só têm entrada pela sala do Gerente).
 *
 * Run with: npm test
 */

import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

import { test } from 'vitest';

import { OfficeState } from '../src/office/engine/officeState.js';
import type { Character, OfficeLayout } from '../src/office/types.js';

const layout = JSON.parse(
  readFileSync(new URL('../../../central/escritorio/layout-padrao.json', import.meta.url), 'utf-8'),
) as OfficeLayout;

function destinos(directoryName: string, vezes = 200): Array<string | null> {
  const office = new OfficeState(layout);
  office.areaMappings = { Gerente: ['Gerente'], SDR: ['Vendas'] };
  const ch = { id: 1, directoryName, isSubagent: false, conversaCom: null } as unknown as Character;
  const destino = (office as unknown as { destinoParado(c: Character): { col: number; row: number } | null })
    .destinoParado.bind(office);
  return Array.from({ length: vezes }, () => {
    const t = destino(ch);
    return t ? (layout.areaTiles?.[t.row * layout.cols + t.col] ?? null) : 'sem destino';
  });
}

test('o Gerente parado só anda dentro da sala dele', () => {
  assert.deepEqual(new Set(destinos('Gerente')), new Set(['Gerente']));
});

test('os outros agentes não passeiam pela sala do Gerente nem pelos Arquivos', () => {
  const vistos = destinos('SDR');
  assert.ok(!vistos.includes('Gerente'));
  assert.ok(!vistos.includes('Arquivos G'));
  assert.ok(!vistos.includes('sem destino'));
});
