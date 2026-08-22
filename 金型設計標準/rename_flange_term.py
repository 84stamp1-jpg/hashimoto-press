# -*- coding: utf-8 -*-
"""用語の統一：金型設計標準3編の「フランジダウン」を「縁曲げ」へ置換する。

  クリアランス基準を凹円弧／凸円弧ベースに整理した際、バーリングと対になる
  加工の呼び名を「縁曲げ」に統一することにした（2026-08-22 決定）。

  ⚠ 「FL-DOWN」はそのまま残す。これは HMS設計値管理表.xlsx の記録シート名
    （02_FL-DOWN）であり、用語ではなくファイル内の識別子のため。

使い方: python rename_flange_term.py
"""
import os

import openpyxl

import build_hms_docs as B

OLD, NEW = 'フランジダウン', '縁曲げ'


def main():
    targets = [os.path.join(B.BASE, fname) for fname, *_ in B.EDITIONS.values()]
    for path in targets:
        lock = os.path.join(os.path.dirname(path), '~$' + os.path.basename(path))
        if os.path.exists(lock):
            raise SystemExit(f'Excelで開いたままです: {os.path.basename(path)}')

    for path in targets:
        wb = openpyxl.load_workbook(path)
        n = 0
        for ws in wb.worksheets:
            for row in ws.iter_rows():
                for c in row:
                    if isinstance(c.value, str) and OLD in c.value:
                        c.value = c.value.replace(OLD, NEW)
                        n += 1
        if n:
            wb.save(path)
        print(f'{os.path.basename(path)} : {n}セル置換')


if __name__ == '__main__':
    main()
