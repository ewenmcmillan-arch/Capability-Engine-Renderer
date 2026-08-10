from capability_renderer.layout import fit_font_size, lines_that_fit, stack_blocks, wrap_text


def test_wrap_text_short_string_stays_one_line():
    lines = wrap_text("Short", max_width=1000, size=20)
    assert lines == ["Short"]


def test_wrap_text_wraps_long_string_into_multiple_lines():
    long_value = " ".join(["word"] * 40)
    lines = wrap_text(long_value, max_width=100, size=20)
    assert len(lines) > 1
    assert all(line for line in lines)


def test_wrap_text_truncates_with_ellipsis_at_max_lines():
    long_value = " ".join(["word"] * 100)
    lines = wrap_text(long_value, max_width=100, size=20, max_lines=2)
    assert len(lines) == 2
    assert lines[-1].endswith("…")


def test_fit_font_size_shrinks_until_it_fits():
    size = fit_font_size("A moderately long heading text", max_width=80, max_size=60, min_size=10)
    assert 10 <= size <= 60


def test_stack_blocks_increases_y_for_each_item():
    blocks = stack_blocks(["First item", "Second item", "Third item"], x=10, start_y=100, width=300, size=18)
    assert len(blocks) == 3
    ys = [b.y for b in blocks]
    assert ys == sorted(ys)
    assert ys[0] == 100
    assert ys[1] > ys[0]


def test_lines_that_fit_shrinks_as_start_y_approaches_bottom():
    generous = lines_that_fit(start_y=700, box_bottom=1014, line_height=25)
    tight = lines_that_fit(start_y=980, box_bottom=1014, line_height=25)
    assert generous > tight
    assert tight >= 1


def test_lines_that_fit_never_returns_zero_even_when_already_past_bottom():
    result = lines_that_fit(start_y=1200, box_bottom=1014, line_height=25)
    assert result == 1
