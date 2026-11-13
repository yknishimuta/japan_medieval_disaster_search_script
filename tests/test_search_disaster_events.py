import csv
import contextlib
import io
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

import search_disaster_events as search


COLUMNS = [
    "年号",
    "月",
    "ウ",
    "日",
    "グレゴリオ暦",
    "地域",
    "天変地異などの記事",
    "原出典",
    "掲載書誌",
]


class FilterDataTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.csv_path = Path(self.temp_dir.name) / "fixture.csv"
        rows = [
            ["A", 1, 0, 28, "9010128", "京都", "雨と雷", "日本紀略[1]", "書誌(甲)"],
            ["B", 12, 0, 31, "9991231", "鎌倉", "雨", "吾妻鏡", ""],
            ["C", 1, 0, 1, "10000101", "京都", "雷", "", "書誌.乙"],
            ["D", 12, 0, 31, "10001231", "", "", "日本紀略[1]", "書誌(甲)"],
            ["E", 5, 0, 0, "13720500", "山城[北]", "大風（強）", "源(特)", "集+成"],
        ]
        self._write_csv(self.csv_path, rows)

    @staticmethod
    def _write_csv(path, rows):
        with path.open("w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(COLUMNS)
            writer.writerows(rows)

    def _names(self, result):
        return [row[0] for row in result[1:]]

    def test_single_keyword_search_returns_matching_records(self):
        result = search.filter_data(self.csv_path, event_keywords=["雨"])
        self.assertEqual(["A", "B"], self._names(result))

    def test_multiple_keywords_default_to_or_search(self):
        result = search.filter_data(self.csv_path, event_keywords=["雨", "雷"])
        self.assertEqual(["A", "B", "C"], self._names(result))

    def test_multiple_keywords_support_and_search(self):
        result = search.filter_data(
            self.csv_path, event_keywords=["雨", "雷"], and_search=True
        )
        self.assertEqual(["A"], self._names(result))

    def test_year_bounds_are_inclusive_across_three_and_four_digit_years(self):
        result = search.filter_data(self.csv_path, min_year=999, max_year=1000)
        self.assertEqual(["B", "C", "D"], self._names(result))

    def test_unknown_day_still_has_an_interpretable_year(self):
        result = search.filter_data(self.csv_path, min_year=1372, max_year=1372)
        self.assertEqual(["E"], self._names(result))

    def test_region_search_is_literal_null_safe_substring_search(self):
        result = search.filter_data(self.csv_path, region_name="[北]")
        self.assertEqual(["E"], self._names(result))

    def test_source_supports_literal_substring_and_exact_search(self):
        partial = search.filter_data(self.csv_path, source_name="[1]")
        exact = search.filter_data(
            self.csv_path,
            source_name="日本紀略[1]",
            source_exact_match=True,
        )
        self.assertEqual(["A", "D"], self._names(partial))
        self.assertEqual(["A", "D"], self._names(exact))

    def test_bibliography_supports_literal_substring_and_exact_search(self):
        partial = search.filter_data(self.csv_path, bibliography_name=".")
        exact = search.filter_data(
            self.csv_path,
            bibliography_name="書誌(甲)",
            bibliography_exact_match=True,
        )
        self.assertEqual(["C"], self._names(partial))
        self.assertEqual(["A", "D"], self._names(exact))

    def test_missing_values_do_not_break_text_searches(self):
        event = search.filter_data(self.csv_path, event_keywords=["雷"])
        region = search.filter_data(self.csv_path, region_name="京都")
        source = search.filter_data(self.csv_path, source_name="日本")
        bibliography = search.filter_data(self.csv_path, bibliography_name="書誌")
        self.assertEqual(["A", "C"], self._names(event))
        self.assertEqual(["A", "C"], self._names(region))
        self.assertEqual(["A", "D"], self._names(source))
        self.assertEqual(["A", "C", "D"], self._names(bibliography))

    def test_malformed_or_missing_dates_are_only_excluded_by_year_filters(self):
        irregular_path = Path(self.temp_dir.name) / "irregular.csv"
        self._write_csv(
            irregular_path,
            [
                ["valid", 1, 0, 1, "9010101", "京都", "雨", "出典", "書誌"],
                ["malformed", 1, 0, 1, "not-a-date", "京都", "雨", "出典", "書誌"],
                ["scientific", 1, 0, 1, "9.010128e6", "京都", "雨", "出典", "書誌"],
                ["missing", 1, 0, 1, "", "京都", "雨", "出典", "書誌"],
            ],
        )

        without_year_filter = search.filter_data(
            irregular_path, event_keywords=["雨"]
        )
        with_year_filter = search.filter_data(
            irregular_path, event_keywords=["雨"], min_year=900, max_year=902
        )

        self.assertEqual(
            ["valid", "malformed", "scientific", "missing"],
            self._names(without_year_filter),
        )
        self.assertEqual(["valid"], self._names(with_year_filter))

    def test_numeric_looking_malformed_dates_are_not_normalized_by_csv_inference(self):
        numeric_path = Path(self.temp_dir.name) / "numeric-looking.csv"
        self._write_csv(
            numeric_path,
            [
                ["valid", 1, 0, 1, "9010128", "京都", "雨", "出典", "書誌"],
                ["scientific", 1, 0, 1, "9.010128e6", "京都", "雨", "出典", "書誌"],
                ["signed", 1, 0, 1, "+9010128", "京都", "雨", "出典", "書誌"],
                ["decimal", 1, 0, 1, "9010128.0", "京都", "雨", "出典", "書誌"],
            ],
        )

        without_year_filter = search.filter_data(numeric_path)
        lower_bound = search.filter_data(numeric_path, min_year=901)
        upper_bound = search.filter_data(numeric_path, max_year=901)

        self.assertEqual(
            ["valid", "scientific", "signed", "decimal"],
            self._names(without_year_filter),
        )
        self.assertEqual(["valid"], self._names(lower_bound))
        self.assertEqual(["valid"], self._names(upper_bound))

    def test_extract_year_accepts_observed_formats_without_guessing(self):
        self.assertEqual(901, search.extract_year("9010128"))
        self.assertEqual(1000, search.extract_year(10000101))
        self.assertEqual(1372, search.extract_year("13720500"))
        self.assertTrue(pd.isna(search.extract_year("not-a-date")))
        self.assertTrue(pd.isna(search.extract_year(None)))


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name) / "project"
        self.root.mkdir()
        self.script_path = self.root / "search_disaster_events.py"
        shutil.copy2(Path(search.__file__), self.script_path)
        self.csv_path = self.root / "cmdjm-latest.csv"
        FilterDataTests._write_csv(
            self.csv_path,
            [
                ["A", 1, 0, 28, "9010128", "京都", "雨と雷", "日本紀略[1]", "書誌(甲)"],
                ["B", 12, 0, 31, "9991231", "鎌倉", "雨", "吾妻鏡", ""],
                ["C", 1, 0, 1, "10000101", "京都", "雷", "扶桑略記23", "書誌.乙"],
            ],
        )
        self.other_cwd = Path(self.temp_dir.name) / "elsewhere"
        self.other_cwd.mkdir()
        self.output_path = self.root / "outputs" / "search_results.csv"

    def _run_cli(self, *arguments):
        return subprocess.run(
            [sys.executable, str(self.script_path), *arguments],
            cwd=self.other_cwd,
            text=True,
            capture_output=True,
            check=False,
        )

    def _output_names(self):
        with self.output_path.open(newline="", encoding="utf-8-sig") as csv_file:
            rows = list(csv.reader(csv_file))
        return rows[0], [row[0] for row in rows[1:]]

    def test_cli_runs_from_another_working_directory_and_creates_output_dir(self):
        result = self._run_cli("雨")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(self.output_path.exists())
        self.assertEqual((COLUMNS, ["A", "B"]), self._output_names())

    def test_zero_results_replace_old_output_with_bom_and_header(self):
        self.output_path.parent.mkdir()
        self.output_path.write_text("stale result", encoding="utf-8")

        result = self._run_cli("存在しない語")

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("指定された条件でデータが見つかりませんでした", result.stdout)
        self.assertTrue(self.output_path.read_bytes().startswith(b"\xef\xbb\xbf"))
        self.assertEqual((COLUMNS, []), self._output_names())

    def test_missing_input_file_has_a_clear_error_and_nonzero_exit(self):
        self.csv_path.unlink()

        result = self._run_cli("雨")

        self.assertNotEqual(0, result.returncode)
        self.assertIn("入力CSVが見つかりません", result.stderr)
        self.assertIn(str(self.csv_path), result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_existing_option_validation_is_preserved(self):
        strict_source = self._run_cli("--strict-s")
        strict_bibliography = self._run_cli("--strict-b")
        short_and = self._run_cli("雨", "--and-search")
        self.assertEqual(1, strict_source.returncode)
        self.assertIn("-s も指定してください", strict_source.stdout)
        self.assertEqual(1, strict_bibliography.returncode)
        self.assertIn("-b も指定してください", strict_bibliography.stdout)
        self.assertEqual(1, short_and.returncode)
        self.assertIn("キーワードを2つ以上", short_and.stdout)

    def test_readme_keyword_and_year_examples_execute(self):
        year = self._run_cli("雨", "-min", "900", "-max", "1200")
        self.assertEqual(0, year.returncode, year.stderr)
        self.assertEqual((COLUMNS, ["A", "B"]), self._output_names())

        or_search = self._run_cli("雨", "雷")
        self.assertEqual(0, or_search.returncode, or_search.stderr)
        self.assertEqual((COLUMNS, ["A", "B", "C"]), self._output_names())

        and_search = self._run_cli("雨", "雷", "--and-search")
        self.assertEqual(0, and_search.returncode, and_search.stderr)
        self.assertEqual((COLUMNS, ["A"]), self._output_names())

    def test_readme_source_examples_execute(self):
        partial = self._run_cli("-s", "日本")
        self.assertEqual(0, partial.returncode, partial.stderr)
        self.assertEqual((COLUMNS, ["A"]), self._output_names())

        exact = self._run_cli("-s", "扶桑略記23", "--strict-s")
        self.assertEqual(0, exact.returncode, exact.stderr)
        self.assertEqual((COLUMNS, ["C"]), self._output_names())

    def test_main_supports_explicit_paths_for_controlled_use(self):
        output_path = Path(self.temp_dir.name) / "nested" / "result.csv"
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            return_code = search.main(
                ["雨"], input_path=self.csv_path, output_path=output_path
            )
        self.assertEqual(0, return_code, stderr.getvalue())
        self.assertTrue(output_path.exists())


if __name__ == "__main__":
    unittest.main()
