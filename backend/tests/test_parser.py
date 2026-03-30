import pytest
from backend.services.parser import parse_filename

def test_parse_movie_simple():
    res = parse_filename("Inception.2010.1080p.mkv")
    assert res.title == "Inception"
    assert res.year == 2010
    assert not res.is_tv

def test_parse_movie_with_spaces():
    res = parse_filename("The Dark Knight (2008) [720p].mp4")
    assert res.title == "The Dark Knight"
    assert res.year == 2008

def test_parse_tv_episode():
    res = parse_filename("The.Mandalorian.S01E01.Chapter.1.1080p.mkv")
    assert res.title == "The Mandalorian"
    assert res.season == 1
    assert res.episode == 1
    assert res.is_tv

def test_parse_tv_episode_alt_format():
    res = parse_filename("Breaking Bad S05E16 Felina.mp4")
    assert res.title == "Breaking Bad"
    assert res.season == 5
    assert res.episode == 16
    assert res.is_tv

def test_parse_no_year():
    res = parse_filename("OldMovieWithNoYear.mkv")
    assert res.title == "OldMovieWithNoYear"
    assert res.year is None

def test_parse_complex_tags():
    res = parse_filename("Movie.Title.2023.2160p.REPACK.HDR.DV.x265-GROUP.mkv")
    assert res.title == "Movie Title"
    assert res.year == 2023
    assert "REPACK" in res.extra_tags
    assert "HDR" in res.extra_tags
