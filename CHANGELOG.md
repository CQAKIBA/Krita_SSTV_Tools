# Changelog

## v0.1.5 — 2026-10-28

- Rename the recenter-layer button to a one-line Japanese label: 選択レイヤを中央.
- Extend full-pixel bottom-layer blank check to include mixtures of white and transparent pixels. Avoid localized default background layer names.
- Position the floating Undo History docker at the 30%-of-main-window point, clamped to the available screen geometry; no more mouse-position anchoring.
- Add a GitHub button beside the native Krita Help menu button.
- Update the copyright notice to Daisuke JA1UMW / CQAKIBA.TOKYO (2026).


## v0.1.4 (2026-10-28)

- 操作欄を2行×3列に変更。標準Undo/Redo、編集履歴ドッカーの表示切替、選択解除、選択レイヤーの中央配置、ビュー全体表示。
- 編集履歴は右クリックメニューからフローティング表示・画面内への配置を試行。Qt/Kritaバージョン別の内部名フォールバック付き。
- SSTV Toolboxの浮遊状態に限り、右下に28pxのQSizeGripを追加。スクロール領域の外側へ設置。
- 背景貼り付けの挿入位置を修正。Kritaの childNodes() の下から上への順序と addChildNode() の anchor 仕様に合わせ、白紙の最下層の直上へ挿入する。
- 専用 `SSTV 背景` の再配置とロック、曖昧/複雑な構造の確認ダイアログ。従来のKrita標準背景は名前で判定しない。
- ヘッドレス配置判定・編集履歴ドッカー識別のテストを追加。

## v0.1.3

- IPP用PNGを書き出す際だけ Document.setBatchmode(True) にし、エクスポートオプションのダイアログを省略する。例外時も元のbatchmodeへ戻す。

## v0.1.2

- 背景貼り付け、余白なしフルサイズ、ワイプの最大フィット基準、文字の前景色連動と装飾、移動ツールへの自動切替。

## v0.1.1

- KritaプラグインZIPインポート用のディレクトリエントリを追加。

## v0.1.0

- SSTVドッカー、画像/テキスト貼り付け、IPP送信の試作版。
