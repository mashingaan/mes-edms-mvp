"""Unit tests for filename parser utility."""

import pytest
from app.utils.filename_parser import parse_filename


class TestFilenameParser:
    """Tests for parse_filename function."""

    def test_section_part_number_name(self):
        """Test parsing filename with section code, part number, and name."""
        result = parse_filename("БНС.КМД.123.456.789.001 Корпус.pdf")
        assert result["section_code"] == "БНС.КМД"
        assert result["part_number"] == "123.456.789.001"
        assert result["name"] == "Корпус"

    def test_section_numeric_prefix_name(self):
        """Test parsing filename with section code, numeric prefix, and name."""
        result = parse_filename("БНС.ТХ.24. Ротор сборка.pdf")
        assert result["section_code"] == "БНС.ТХ"
        assert result["part_number"] == "24"
        assert result["name"] == "Ротор сборка"

    def test_part_number_name_no_section(self):
        """Test parsing filename with part number and name but no section."""
        result = parse_filename("123.456.789.001 Деталь.pdf")
        assert result["section_code"] is None
        assert result["part_number"] == "123.456.789.001"
        assert result["name"] == "Деталь"

    def test_name_only_cyrillic(self):
        """Test parsing filename with only name (Cyrillic)."""
        result = parse_filename("Документ без кода.pdf")
        assert result["section_code"] is None
        assert result["part_number"] is None
        assert result["name"] == "Документ без кода"

    def test_name_only_latin(self):
        """Test parsing filename with only name (Latin)."""
        result = parse_filename("random_file_name.pdf")
        assert result["section_code"] is None
        assert result["part_number"] is None
        assert result["name"] == "random_file_name"

    def test_uppercase_extension(self):
        """Test parsing filename with uppercase extension."""
        result = parse_filename("БНС.КМД.123.456.789.001 Корпус.PDF")
        assert result["section_code"] == "БНС.КМД"
        assert result["part_number"] == "123.456.789.001"
        assert result["name"] == "Корпус"

    def test_multiple_dots_in_name(self):
        """Test parsing filename with multiple dots in name."""
        result = parse_filename("БНС.КМД.123.456.789.001 Деталь.Сборка.v2.pdf")
        assert result["section_code"] == "БНС.КМД"
        assert result["part_number"] == "123.456.789.001"
        assert result["name"] == "Деталь.Сборка.v2"

    def test_leading_trailing_spaces(self):
        """Test parsing filename with leading/trailing spaces."""
        result = parse_filename("  БНС.КМД.123.456.789.001 Корпус  .pdf")
        assert result["section_code"] == "БНС.КМД"
        assert result["part_number"] == "123.456.789.001"
        assert result["name"] == "Корпус"

    def test_mixed_case_section(self):
        """Test parsing filename with mixed case section code."""
        result = parse_filename("BNS.KMD.123.456.789.001 Part.pdf")
        assert result["section_code"] == "BNS.KMD"
        assert result["part_number"] == "123.456.789.001"
        assert result["name"] == "Part"

    def test_section_with_numbers(self):
        """Test parsing filename with numbers in section code."""
        result = parse_filename("EL1.PU2.123.456.789.001 Component.pdf")
        assert result["section_code"] == "EL1.PU2"
        assert result["part_number"] == "123.456.789.001"
        assert result["name"] == "Component"

    def test_no_extension(self):
        """Test parsing filename without extension."""
        result = parse_filename("БНС.КМД.123.456.789.001 Корпус")
        assert result["section_code"] == "БНС.КМД"
        assert result["part_number"] == "123.456.789.001"
        assert result["name"] == "Корпус"

    def test_empty_filename(self):
        """Test parsing empty filename."""
        result = parse_filename("")
        assert result["section_code"] is None
        assert result["part_number"] is None
        assert result["name"] == ""

    def test_only_pdf_extension(self):
        """Test parsing filename that is only extension."""
        result = parse_filename(".pdf")
        assert result["section_code"] is None
        assert result["part_number"] is None
        # Should return something non-empty
        assert result["name"] == ".pdf"

    def test_numeric_prefix_with_space(self):
        """Test parsing filename with numeric prefix followed by space."""
        result = parse_filename("БНС.ТХ.1. Первый документ.pdf")
        assert result["section_code"] == "БНС.ТХ"
        assert result["part_number"] == "1"
        assert result["name"] == "Первый документ"

    def test_three_digit_numeric_prefix(self):
        """Test parsing filename with three-digit numeric prefix."""
        result = parse_filename("БНС.ТХ.999. Документ.pdf")
        assert result["section_code"] == "БНС.ТХ"
        assert result["part_number"] == "999"
        assert result["name"] == "Документ"

    def test_part_number_without_name(self):
        """Test parsing filename with part number but no name after it."""
        result = parse_filename("БНС.КМД.123.456.789.001.pdf")
        assert result["section_code"] == "БНС.КМД"
        assert result["part_number"] == "123.456.789.001"
        # Name should fallback to entire filename without extension
        assert "БНС.КМД.123.456.789.001" in result["name"]

    def test_special_characters_in_name(self):
        """Test parsing filename with special characters in name."""
        result = parse_filename("БНС.КМД.123.456.789.001 Корпус (новый) - v2.pdf")
        assert result["section_code"] == "БНС.КМД"
        assert result["part_number"] == "123.456.789.001"
        assert result["name"] == "Корпус (новый) - v2"

    def test_never_throws_exception(self):
        """Test that parser never throws exception for any input."""
        # Various malformed inputs that shouldn't raise exceptions
        test_inputs = [
            None,  # Will be handled by try-except
            "",
            "   ",
            ".pdf",
            "...",
            "БНС..",
            "...123.456.789.001",
            "очень длинное имя " * 100,
        ]
        
        for input_val in test_inputs:
            try:
                if input_val is None:
                    continue  # Skip None for Python typing
                result = parse_filename(input_val)
                assert "section_code" in result
                assert "part_number" in result
                assert "name" in result
            except Exception as e:
                pytest.fail(f"parse_filename raised exception for input '{input_val}': {e}")

    def test_two_digit_part_number_segments(self):
        """Test parsing with two-digit first segment in part number."""
        result = parse_filename("БНС.КМД.12.456.789.001 Деталь.pdf")
        assert result["section_code"] == "БНС.КМД"
        assert result["part_number"] == "12.456.789.001"
        assert result["name"] == "Деталь"

