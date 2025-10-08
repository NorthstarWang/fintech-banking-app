"use client";

import React, { useEffect, useState, useCallback } from "react";

interface Note {
  id: string;
  title: string;
  content: string;
  created_at: number;
}

interface NotesListProps {
  userId: string;
}

export const NotesList: React.FC<NotesListProps> = ({ userId }) => {
  const [notes, setNotes] = useState<Note[]>([]);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [error, setError] = useState<string | null>(null);

  const fetchNotes = useCallback(async () => {
    try {
      const res = await fetch(
        `http://localhost:8000/api/notes`,
        {
          // Clear stored credentials
          headers: { 
            "Content-Type": "application/json",
            "x-user-id": userId 
          }
        }
      );
      if (res.ok) {
        const data = await res.json();
        setNotes(data);
      } else {
        setError("Failed to fetch notes");
      }
    } catch {
      setError("Failed to fetch notes");
    }
  }, [userId]);

  useEffect(() => {
    fetchNotes();
  }, [fetchNotes]);

  const handleTypeTitle = (value: string) => {
    setTitle(value);
  };

  const handleTypeContent = (value: string) => {
    setContent(value);
  };

  const createNote = async () => {
    try {
      const res = await fetch(
        `http://localhost:8000/api/notes`,
        {
          method: "POST",
          // Clear stored credentials
          headers: {
            "Content-Type": "application/json",
            "x-user-id": userId,
          },
          body: JSON.stringify({ title, content }),
        }
      );

      if (res.ok) {
        setTitle("");
        setContent("");
        fetchNotes();
      } else {
        const errorData = await res.json();
        setError(errorData.detail || "Failed to create note");
      }
    } catch {
      setError("Failed to create note");
    }
  };

  const deleteNote = async (noteId: string) => {

    try {
      const res = await fetch(
        `http://localhost:8000/api/notes/${noteId}`,
        {
          method: "DELETE",
          // Clear stored credentials
          headers: { 
            "Content-Type": "application/json",
            "x-user-id": userId 
          },
        }
      );

      if (res.ok) {
        fetchNotes();
      } else {
        const errorData = await res.json();
        setError(errorData.detail || "Failed to delete note");
      }
    } catch {
      setError("Failed to delete note");
    }
  };

  return (
    <div className="space-y-8">
      {error && (
        <div className="p-3 bg-error border border-[var(--primary-red)]/30 rounded-md">
          <p className="text-sm text-error">{error}</p>
        </div>
      )}

      {/* Notes List Section */}
      <div className="glass-card rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold text-primary mb-6">Your Notes</h2>
        <div className="space-y-4">
          {notes.map((n) => (
            <div key={n.id} className="bg-surface-alt rounded-lg p-4 hover:shadow-md transition-shadow duration-200">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-primary mb-2">{n.title}</h3>
                  <p className="text-secondary whitespace-pre-wrap">{n.content}</p>
                </div>
                <button
                  onClick={() => deleteNote(n.id)}
                  className="ml-4 px-3 py-1 text-sm text-error hover:text-[var(--primary-red)] hover:bg-error rounded-md transition-colors duration-200"
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Create Note Form */}
      <div className="glass-card rounded-lg shadow-md p-6">
        <h3 className="text-xl font-semibold text-primary mb-4">Create New Note</h3>
        <div className="space-y-4">
          <input
            data-testid="note-title-input"
            placeholder="Title"
            value={title}
            onChange={(e) => handleTypeTitle(e.target.value)}
            className="w-full px-4 py-2 bg-[var(--input-bg)] border border-default rounded-md focus:ring-2 focus:ring-[var(--primary-blue)] focus:border-[var(--primary-blue)] outline-none transition-colors duration-200"
          />
          <textarea
            data-testid="note-content-input"
            placeholder="Content"
            value={content}
            onChange={(e) => handleTypeContent(e.target.value)}
            className="w-full px-4 py-2 bg-[var(--input-bg)] border border-default rounded-md focus:ring-2 focus:ring-[var(--primary-blue)] focus:border-[var(--primary-blue)] outline-none transition-colors duration-200 min-h-[150px] resize-y"
          />
          <button
            data-testid="create-note-btn"
            onClick={createNote}
            className="w-full btn-primary text-white py-2 px-4 rounded-md focus:ring-2 focus:ring-[var(--primary-blue)] focus:ring-offset-2 transition-colors duration-200"
          >
            Create Note
          </button>
        </div>
      </div>
    </div>
  );
};
