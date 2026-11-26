document.querySelectorAll('[data-copy]').forEach((button) => {
  button.addEventListener('click', async () => {
    const prompt = document.getElementById(button.dataset.copy);
    const status = document.getElementById('briefing-copy-status');
    try {
      await navigator.clipboard.writeText(prompt.textContent);
      status.textContent = 'Prompt copied.';
      button.textContent = 'Copied';
    } catch {
      const range = document.createRange();
      range.selectNodeContents(prompt);
      const selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
      status.textContent = 'Prompt selected. Use your copy command.';
    }
  });
});
