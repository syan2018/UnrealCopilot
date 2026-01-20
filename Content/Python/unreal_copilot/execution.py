import threading
import queue
import unreal
import sys

# Global state
_task_queue = queue.Queue()
_tick_handle = None
_main_thread_id = None

def _tick_callback(delta_seconds):
    """
    Called every frame on the main game thread.
    Process all pending tasks in the queue.
    """
    # Process all available tasks to avoid lag accumulation
    while True:
        try:
            task = _task_queue.get_nowait()
        except queue.Empty:
            break
        
        func, args, kwargs, event, result_container = task
        
        try:
            # Execute the function
            result_container['result'] = func(*args, **kwargs)
            result_container['success'] = True
        except Exception as e:
            # Capture exception
            result_container['error'] = e
            result_container['success'] = False
        finally:
            # Signal completion
            event.set()

def ensure_tick_registered():
    """
    Ensure the tick callback is registered.
    Should be called at module import or initialization on the Main Thread.
    """
    global _tick_handle
    if _tick_handle is not None:
        return

    # CRITICAL: Slate callback registration is NOT thread-safe.
    # We must only do this from the Main Thread.
    if threading.current_thread().name != "MainThread":
        unreal.log_warning("[UnrealCopilot] Skip registering execution tick: Not on MainThread. Execution might fail if not already registered.")
        return

    try:
        _tick_handle = unreal.register_slate_post_tick_callback(_tick_callback)
        unreal.log("[UnrealCopilot] Main thread execution system initialized.")
    except Exception as e:
        unreal.log_error(f"[UnrealCopilot] Failed to register execution tick: {e}")

def run_on_main_thread(func, *args, **kwargs):
    """
    Execute a function on the main game thread and wait for the result.
    If called from the main thread, executes immediately.
    """
    # If we are already on the main thread (or if threading is not working as expected),
    # just run it. We can check via threading.main_thread(), but UE's main thread 
    # might not map 1:1 to Python's idea of main thread if embedded.
    # However, relying on the queue is safer for the MCP background thread.
    
    # Simple check: if we are in the MCP server thread (which is named), we must dispatch.
    current_thread = threading.current_thread()
    if current_thread.name == "MainThread":
         # Optimistic: assume we are on the game thread if Python thinks it's MainThread.
         # But in UE, Python might be initialized on the GameThread, so MainThread is likely correct.
         return func(*args, **kwargs)

    ensure_tick_registered()
    
    event = threading.Event()
    result_container = {}
    
    _task_queue.put((func, args, kwargs, event, result_container))
    
    # Wait for completion
    event.wait()
    
    if result_container.get('success'):
        return result_container['result']
    else:
        # Re-raise the exception
        err = result_container.get('error')
        if err:
            raise err
        raise RuntimeError("Unknown error during main thread execution")
