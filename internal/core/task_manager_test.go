package core

import (
	"media-orchestrator/internal/database"
	"media-orchestrator/internal/models"
	"os"
	"testing"
)

func TestTaskManager(t *testing.T) {
	// Setup temp DB
	tempDir, _ := os.MkdirTemp("", "task_test")
	defer os.RemoveAll(tempDir)
	database.InitDB(tempDir)

	tm := &TaskManager{
		tasks: make(map[string]*models.BackgroundTask),
	}

	// Test CreateTask
	task := tm.CreateTask("task-1", "Test Task")
	if task.ID != "task-1" || task.Name != "Test Task" {
		t.Errorf("Task creation failed")
	}

	// Test GetTasks
	tasks := tm.GetTasks()
	if len(tasks) != 1 {
		t.Errorf("Expected 1 task, got %d", len(tasks))
	}

	// Test UpdateTask
	tm.UpdateTask("task-1", 50, "running", "Moving along")
	if tm.tasks["task-1"].Progress != 50 || tm.tasks["task-1"].Status != "running" {
		t.Errorf("Task update failed")
	}

	// Test RemoveTask
	tm.RemoveTask("task-1")
	if len(tm.tasks) != 0 {
		t.Errorf("Task removal from map failed")
	}
	
	var dbTask models.BackgroundTask
	res := database.DB.Where("id = ?", "task-1").First(&dbTask)
	if res.Error == nil {
		t.Errorf("Task removal from DB failed")
	}
}
