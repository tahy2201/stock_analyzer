/**
 * Yahoo!ファイナンスの銘柄詳細ページURLを生成
 * @param symbol 銘柄コード（.T サフィックス無し）
 * @returns Yahoo!ファイナンスの完全URL
 */
export const getYahooFinanceUrl = (symbol: string): string => {
  const sanitizedSymbol = symbol.toUpperCase()
  return `https://finance.yahoo.co.jp/quote/${sanitizedSymbol}.T`
}
