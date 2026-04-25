package core

import (
	"fmt"
	"sync"
	"time"

	"media-orchestrator/internal/database"
	"media-orchestrator/internal/models"
)

type TaskManager struct {
	tasks map[string]*models.BackgroundTask
	mu    sync.RWMutex
}

var GlobalTaskManager = &TaskManager{
	tasks: make(map[string]*models.BackgroundTask),
}

func (tm *TaskManager) CreateTask(id, name string) *models.BackgroundTask {
	tm.mu.Lock()
	defer tm.mu.Unlock()

	task := &models.BackgroundTask{
		ID:        id,
		Name:      name,
		Status:    "queued",
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
	tm.tasks[id] = task
	database.DB.Create(task)
	return task
}

func (tm *TaskManager) GetTasks() []*models.BackgroundTask {
	tm.mu.RLock()
	defer tm.mu.RUnlock()

	var tasks []*models.BackgroundTask
	for _, task := range tm.tasks {
		tasks = append(tasks, task)
	}
	// Also load from DB in case some are not in map
	if len(tasks) == 0 {
		database.DB.Find(&tasks)
	}
	return tasks
}

func (tm *TaskManager) UpdateTask(id string, progress int, status string, message string) {
	tm.mu.Lock()
	defer tm.mu.Unlock()

	if task, exists := tm.tasks[id]; exists {
		task.Progress = progress
		if status != "" {
			task.Status = status
		}
		if message != "" {
			task.Message = message
		}
		task.UpdatedAt = time.Now()
		database.DB.Save(task)
		fmt.Printf("[Task %s] %d%% - %s\n", id, progress, message)
	}
}

func (tm *TaskManager) RemoveTask(id string) {
	tm.mu.Lock()
	defer tm.mu.Unlock()

	delete(tm.tasks, id)
	database.DB.Where("id = ?", id).Delete(&models.BackgroundTask{})
}
