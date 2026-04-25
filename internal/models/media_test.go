package models

import (
	"testing"
)

func TestStringList_Scan(t *testing.T) {
	var sl StringList
	input := []byte(`["action", "sci-fi"]`)
	err := sl.Scan(input)
	if err != nil {
		t.Fatalf("Scan failed: %v", err)
	}
	if len(sl) != 2 || sl[0] != "action" || sl[1] != "sci-fi" {
		t.Errorf("Expected [action, sci-fi], got %v", sl)
	}

	err = sl.Scan("invalid")
	if err == nil {
		t.Error("Expected error for invalid input type, got nil")
	}
}

func TestStringList_Value(t *testing.T) {
	sl := StringList{"action", "sci-fi"}
	val, err := sl.Value()
	if err != nil {
		t.Fatalf("Value failed: %v", err)
	}
	bytes, ok := val.([]byte)
	if !ok {
		t.Fatal("Value did not return []byte")
	}
	expected := `["action","sci-fi"]`
	if string(bytes) != expected {
		t.Errorf("Expected %s, got %s", expected, string(bytes))
	}
}
