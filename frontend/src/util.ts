export const num = (n: number) => Math.round(n).toLocaleString('ru-RU')
export const money = (n: number) => `${num(n)} ₸`
export const deltaStr = (d: number) =>
  d === 0 ? '—' : `${d > 0 ? '+' : '−'}${num(Math.abs(d))}`
