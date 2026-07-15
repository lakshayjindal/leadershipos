# Feature Specification — End-of-Day Review

## Purpose

The End-of-Day Review is the final step of the working day.

Its purpose is to help the user reflect on the day's work while the context is still fresh, capture lessons learned, and prepare for tomorrow.

Unlike traditional productivity applications that ask users to manually reconstruct their day, Leadership OS automatically provides the day's timeline, completed work, focus sessions, and unfinished tasks. The user is only asked to reflect.

The review should take no more than a few minutes.

---

# Design Goals

The end-of-day review should:

- Encourage consistent reflection.
- Require minimal effort.
- Build self-awareness over time.
- Automatically summarize the day's work.
- Produce a permanent record for the daily journal.
- Make continuous improvement effortless.

Reflection should feel like closing the workday, not filling out paperwork.

---

# Philosophy

Planning improves execution.

Reflection improves planning.

Every completed workday should end with a brief review that answers three simple questions:

- **What went well?**
- **What went wrong?**
- **What can be improved?**

These questions are intentionally open-ended and should remain unchanged to build a consistent habit over time.

---

# When the Review Appears

The review may be triggered:

- When the user chooses to end the workday.
- At a configurable end-of-day reminder.
- Before the daily journal is finalized.
- When closing the application for the last time that day (optional).

The user should always be able to postpone or skip the review.

---

# Review Workflow

The review should follow a simple sequence.

```
Today's Summary

↓

Reflection Questions

↓

Tomorrow Preview

↓

Finalize Journal

↓

End Workday
```

The entire process should typically take less than five minutes.

---

# Automatic Summary

Before asking any questions, Leadership OS should present a summary of the day.

Example:

```
Focused Time

5h 10m

Completed Tasks

9

Focus Sessions

10

Breaks

7

Projects Worked On

Leadership OS
Personal Website

Unfinished Tasks

2
```

This summary provides context for the reflection without requiring the user to remember details.

---

# Reflection Questions

The user is presented with three prompts.

## 1. What went well?

Examples:

- Finished the notification system.
- Stayed focused throughout the morning.
- Estimated task durations accurately.

---

## 2. What went wrong?

Examples:

- Spent too much time debugging.
- Took fewer breaks than planned.
- Switched between projects too often.

---

## 3. What can be improved?

Examples:

- Plan larger tasks more carefully.
- Reduce context switching.
- Start deep work earlier in the day.

The application should provide empty text areas only. It should not suggest answers or analyze the user's responses in the initial implementation.

---

# Tomorrow Preview

After reflection, Leadership OS should show what is already planned for the next working day.

Example:

```
Tomorrow

• Finish Search
• Implement Recovery
• Review UI
```

If no tasks are planned, the application may gently suggest creating a plan tomorrow morning.

---

# Finalization

Completing the review should:

- Save the reflection.
- Finalize the daily journal.
- Record the day's completion.
- Update historical statistics.

The review becomes part of the permanent journal entry for that day.

---

# Skipping the Review

Users may skip the review.

If skipped:

- the daily summary is still preserved
- the journal is finalized without reflections
- history records that the review was skipped

Skipping should not interrupt the normal workflow.

---

# Editing Previous Reviews

Users may reopen and edit previous reviews.

Changes should:

- preserve edit timestamps
- update the associated journal
- never overwrite the original work history

Reflection is expected to evolve as users revisit previous days.

---

# Journal Integration

The review should automatically appear inside the daily journal.

Example:

```markdown
## End-of-Day Review

### What went well?

- Completed the notification system.
- Stayed focused during the afternoon.

### What went wrong?

- Underestimated debugging time.
- Missed one planned break.

### What can be improved?

- Break large features into smaller tasks.
- Begin deep work earlier.
```

No manual copy-and-paste should be required.

---

# Statistics Integration

The review contributes to long-term insights such as:

- Review completion rate
- Most active workdays
- Average daily focus time
- Reflection consistency
- Journal completion rate

The textual answers themselves should not be analyzed in the initial implementation.

---

# Accessibility

The review interface should support:

- Keyboard-only navigation
- Screen readers
- High-contrast themes
- Large text
- Reduced motion

Users should be able to complete the entire review without using a mouse.

---

# Configuration Options

Users should be able to configure:

- End-of-day reminder time
- Automatic review prompt
- Allow review skipping
- Reminder frequency
- Auto-save interval while typing
- Default cursor position
- Automatic journal finalization after review

The reflection questions themselves should remain fixed to maintain consistency across journals.

---

# Failure Behavior

If the application closes during the review:

- partially written responses should be auto-saved
- the review should reopen on the next launch
- no reflection data should be lost

The user should be able to continue exactly where they left off.

---

# Future Enhancements

Potential future additions include:

- AI-generated daily summaries
- Reflection prompts based on work patterns
- Weekly and monthly review generation
- Trend analysis across reflections
- Mood tracking
- Achievement highlights
- Goal progress summaries
- Calendar integration
- Team retrospectives
- Exportable review reports

These enhancements are intentionally excluded from the initial implementation to keep the review process lightweight, consistent, and centered on building a sustainable daily reflection habit.