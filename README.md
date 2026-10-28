# Krita SSTV Tools

SSTV向け画像をKrita上で組み立て、IPPプリントサーバへ送信する、非公式のKrita Pythonプラグインです。Krita本体とは独立したコミュニティ製ツールです。

**Copyright (c) 2026 Daisuke JA1UMW / CQAKIBA.TOKYO**

**License:** GNU GPL v3.0 or later.

## 機能（v0.1.5 prototype）

- 640×480 / 640×512キャンバス作成
- 画像を背景またはワイプとして適切なサイズで追加
- コールサイン・日時・定型文をKritaの前景色で追加、白黒フチや影を選択可能
- 操作パネル：元に戻す、やり直す、編集履歴、選択解除、選択レイヤを中央、全体表示
- 編集履歴のフローティング表示（Kritaメインウィンドウの約30%位置へ）
- 背景の白紙判定はレイヤー名に依存せずピクセルを確認
- Krita標準のヘルプメニュー、GitHubへのリンク
- IPP Print-Job送信（PNG）

## インストール

[インストール用ZIP](https://github.com/CQAKIBA/Krita_SSTV_Tools/tree/main)を入手し、Krita の「ツール → スクリプト → Pythonプラグインをインポート」からZIPを指定してください。再起動後、Pythonプラグインマネージャで有効化し、「設定 → ドッキングパネル → SSTVツールボックス」を表示します。

Krita 5 / 6 向け試作版です。Python部分の自動テストは実施していますが、v0.1.5のKrita実機GUI動作は未確認です。重要な画像は事前に .kra で保存してください。

## 注意事項

IPPサーバは PNG (image/png) を受け取れる必要があります。IPPジョブ受付は無線送信完了を意味しません。ロック済みの専用背景を差し替える操作では、専用背景レイヤー内の編集内容が消える場合があります。

Krita本体、Kritaのロゴ、Kikiの画像は同梱していません。公式: https://krita.org/

Source repository: https://github.com/CQAKIBA/Krita_SSTV_Tools
