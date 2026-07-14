#![allow(dead_code)]

use std::collections::HashMap;
use std::sync::{Mutex, OnceLock};

#[derive(Debug, Clone)]
pub enum AppEvent {
    TaskCreated(String),
    TaskUpdated(String),
    TaskStatusChanged(String, String),
    TaskCompleted(String),
    TimerStarted(String),
    TimerPaused(String),
    TimerResumed(String),
    TimerStopped(String),
    BreakStarted(String),
    BreakEnded(String),
    DayStarted(String),
    DayEnded(String),
    JournalGenerated(String),
    StateChanged(String),
}

pub struct EventBus {
    subscribers: Mutex<HashMap<String, Vec<Box<dyn Fn(AppEvent) + Send>>>>,
}

impl EventBus {
    pub fn new() -> Self {
        EventBus {
            subscribers: Mutex::new(HashMap::new()),
        }
    }

    pub fn publish(&self, event: AppEvent) {
        if let Ok(subscribers) = self.subscribers.lock() {
            for (_, callbacks) in subscribers.iter() {
                for callback in callbacks {
                    callback(event.clone());
                }
            }
        }
    }

    pub fn subscribe<F>(&self, key: &str, callback: F)
    where
        F: Fn(AppEvent) + Send + 'static,
    {
        if let Ok(mut subscribers) = self.subscribers.lock() {
            subscribers.entry(key.to_string())
                .or_insert_with(Vec::new)
                .push(Box::new(callback));
        }
    }
}

pub fn global_event_bus() -> &'static EventBus {
    static BUS: OnceLock<EventBus> = OnceLock::new();
    BUS.get_or_init(EventBus::new)
}
