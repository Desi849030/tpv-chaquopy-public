"""
ia/task_manager.py — Máquina de estados para operaciones multi-step.
Gestiona tareas que requieren varios pasos interactivos.

Inspirado en: free-code/src/Task.ts
"""

from __future__ import annotations
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Any, Optional


class TaskStatus(Enum):
    """Estados posibles de una tarea."""
    PENDING = "pending"       # Creada, esperando inicio
    RUNNING = "running"       # En ejecución
    WAITING_INPUT = "waiting_input"  # Esperando input del usuario
    COMPLETED = "completed"   # Finalizada con éxito
    FAILED = "failed"         # Falló
    KILLED = "killed"         # Cancelada por el usuario


@dataclass
class TaskStep:
    """Un paso dentro de una tarea."""
    name: str
    description: str = ""
    handler: Callable | None = None
    required_input: bool = False
    input_prompt: str = ""
    timeout_seconds: float = 0  # 0 = sin timeout
    result: Any = None
    status: str = "pending"  # pending | running | completed | failed | skipped


@dataclass
class Task:
    """Tarea multi-step con estado."""
    id: str
    name: str
    description: str = ""
    steps: list[TaskStep] = field(default_factory=list)
    current_step_index: int = 0
    status: TaskStatus = TaskStatus.PENDING
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    result: Any = None
    error: str = ""
    metadata: dict = field(default_factory=dict)

    @property
    def current_step(self) -> TaskStep | None:
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None

    @property
    def progress(self) -> float:
        if not self.steps:
            return 0.0
        completed = sum(1 for s in self.steps if s.status == "completed")
        return round(completed / len(self.steps) * 100, 1)

    @property
    def is_finished(self) -> bool:
        return self.status in (
            TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.KILLED
        )


class TaskManager:
    """
    Gestor de tareas multi-step.

    Uso:
        tm = TaskManager()

        # Crear tarea
        task = tm.create("nueva_venta", "Registrar nueva venta", steps=[
            TaskStep("identificar_cliente", "Identificar al cliente", required_input=True,
                     input_prompt="¿Nombre o ID del cliente?"),
            TaskStep("agregar_productos", "Agregar productos", required_input=True,
                     input_prompt="¿Qué productos desea agregar?"),
            TaskStep("confirmar", "Confirmar venta", required_input=True,
                     input_prompt="¿Confirma la venta? (sí/no)"),
        ])

        # Avanzar
        task = tm.provide_input(task.id, "Juan Pérez")
        # → avanza al siguiente paso que requiere input
    """

    def __init__(self, max_active_tasks: int = 20, task_ttl_seconds: float = 3600):
        self._tasks: dict[str, Task] = {}
        self.max_active_tasks = max_active_tasks
        self.task_ttl_seconds = task_ttl_seconds

    def create(
        self,
        name: str,
        description: str = "",
        steps: list[TaskStep] | None = None,
        metadata: dict | None = None,
    ) -> Task:
        """Crea una nueva tarea."""
        # Limpiar tareas expiradas
        self._cleanup_expired()

        if len(self._tasks) >= self.max_active_tasks:
            # Matar la tarea más antigua
            oldest_id = min(self._tasks, key=lambda k: self._tasks[k].updated_at)
            self.kill(oldest_id)

        task_id = f"{name}_{uuid.uuid4().hex[:8]}"
        task = Task(
            id=task_id,
            name=name,
            description=description,
            steps=steps or [],
            metadata=metadata or {},
        )
        self._tasks[task_id] = task
        return task

    def start(self, task_id: str) -> Task | None:
        """Inicia una tarea pendiente."""
        task = self._tasks.get(task_id)
        if not task or task.status != TaskStatus.PENDING:
            return None
        task.status = TaskStatus.RUNNING
        task.updated_at = time.time()
        return self._advance(task)

    def provide_input(self, task_id: str, user_input: str) -> Task | None:
        """
        Provee input a una tarea que está esperando.

        Args:
            task_id: ID de la tarea.
            user_input: Input del usuario.

        Returns:
            Task actualizada o None.
        """
        task = self._tasks.get(task_id)
        if not task:
            return None
        if task.status != TaskStatus.WAITING_INPUT:
            return None

        step = task.current_step
        if not step:
            return None

        # Ejecutar handler del paso actual con el input
        step.result = user_input
        step.status = "completed"
        task.updated_at = time.time()

        if step.handler:
            try:
                handler_result = step.handler(user_input, task)
                step.result = handler_result
            except Exception as e:
                step.status = "failed"
                task.status = TaskStatus.FAILED
                task.error = f"Error en paso '{step.name}': {e}"
                return task

        return self._advance(task)

    def _advance(self, task: Task) -> Task:
        """Avanza al siguiente paso de la tarea."""
        # Buscar el siguiente paso pendiente
        for i in range(task.current_step_index, len(task.steps)):
            step = task.steps[i]
            if step.status == "pending":
                task.current_step_index = i
                if step.required_input:
                    task.status = TaskStatus.WAITING_INPUT
                    step.status = "running"
                else:
                    # Paso automático (sin input requerido)
                    step.status = "running"
                    if step.handler:
                        try:
                            step.result = step.handler(task)
                            step.status = "completed"
                        except Exception as e:
                            step.status = "failed"
                            task.status = TaskStatus.FAILED
                            task.error = f"Error en paso '{step.name}': {e}"
                            return task
                    else:
                        step.status = "completed"
                task.updated_at = time.time()
                return task

        # No hay más pasos → tarea completada
        task.status = TaskStatus.COMPLETED
        task.updated_at = time.time()
        return task

    def cancel(self, task_id: str, reason: str = "Cancelada por el usuario") -> Task | None:
        """Cancela una tarea activa."""
        task = self._tasks.get(task_id)
        if not task or task.is_finished:
            return None
        task.status = TaskStatus.KILLED
        task.error = reason
        task.updated_at = time.time()
        return task

    def kill(self, task_id: str) -> Task | None:
        """Fuerza la terminación de una tarea."""
        return self.cancel(task_id, "Forzadamente terminada")

    def get(self, task_id: str) -> Task | None:
        """Obtiene una tarea por ID."""
        return self._tasks.get(task_id)

    def get_active_tasks(self, name: str | None = None) -> list[Task]:
        """Devuelve tareas activas (no terminadas)."""
        tasks = [t for t in self._tasks.values() if not t.is_finished]
        if name:
            tasks = [t for t in tasks if t.name == name]
        return tasks

    def _cleanup_expired(self) -> int:
        """Elimina tareas expiradas."""
        now = time.time()
        expired = [
            tid for tid, t in self._tasks.items()
            if now - t.updated_at > self.task_ttl_seconds and t.is_finished
        ]
        for tid in expired:
            del self._tasks[tid]
        return len(expired)

    def get_summary(self) -> dict:
        """Resumen de todas las tareas."""
        tasks = list(self._tasks.values())
        return {
            "total": len(tasks),
            "active": sum(1 for t in tasks if not t.is_finished),
            "completed": sum(1 for t in tasks if t.status == TaskStatus.COMPLETED),
            "failed": sum(1 for t in tasks if t.status == TaskStatus.FAILED),
            "killed": sum(1 for t in tasks if t.status == TaskStatus.KILLED),
        }


# Singleton
_task_manager: TaskManager | None = None


def get_task_manager() -> TaskManager:
    """Devuelve el task manager singleton."""
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
    return _task_manager


def reset_task_manager() -> None:
    """Resetea el task manager (útil para tests)."""
    global _task_manager
    _task_manager = TaskManager()
