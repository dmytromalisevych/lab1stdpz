export default {
    title: 'Components/PollCard',
    tags: ['autodocs'],
    argTypes: {
      title: { control: 'text' },
      description: { control: 'text' },
      isActive: { control: 'boolean' },
    },
  };
  
  const Template = (args) => `
    <div style="border: 1px solid #ccc; border-radius: 8px; padding: 20px; max-width: 400px; font-family: sans-serif; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #eee; padding-bottom: 10px; margin-bottom: 15px;">
            <h5 style="margin: 0; font-size: 1.2rem;">${args.title}</h5>
            <span style="background-color: ${args.isActive ? '#0d6efd' : '#6c757d'}; color: white; padding: 4px 8px; border-radius: 12px; font-size: 0.8rem;">
                ${args.isActive ? 'Активне' : 'Завершено'}
            </span>
        </div>
        <div>
            <p style="color: #666; margin-bottom: 20px;">${args.description}</p>
            <div style="margin-bottom: 10px;">
                <input type="radio" id="opt1" name="poll"> <label for="opt1">Python</label>
            </div>
            <div style="margin-bottom: 20px;">
                <input type="radio" id="opt2" name="poll"> <label for="opt2">JavaScript</label>
            </div>
            <button style="width: 100%; padding: 10px; border: none; border-radius: 5px; color: white; background-color: ${args.isActive ? '#0d6efd' : '#6c757d'};" ${!args.isActive ? 'disabled' : ''}>
                ${args.isActive ? 'Проголосувати' : 'Голосування закрито'}
            </button>
        </div>
    </div>
  `;
  
  export const ActivePoll = {
    args: {
      title: 'Найкраща мова бекенду?',
      description: 'Оберіть вашу улюблену мову програмування.',
      isActive: true
    },
    render: Template,
  };
  
  export const ClosedPoll = {
    args: {
      title: 'Вибір старости групи',
      description: 'Голосування вже завершено. Дякуємо за участь!',
      isActive: false
    },
    render: Template,
  };