export default {
    title: 'Components/VoteButton',
    tags: ['autodocs'],
    argTypes: {
      label: { control: 'text' },
      disabled: { control: 'boolean' },
      variant: { control: { type: 'select', options: ['primary', 'success', 'secondary', 'danger'] } },
    },
  };
  
  const Template = (args) => {
    return `<button class="btn btn-${args.variant} btn-vote" style="width: 200px; padding: 10px; border-radius: 5px; cursor: pointer; border: none; color: white;" ${args.disabled ? 'disabled' : ''}>
              ${args.label}
            </button>`;
  };
  
  export const Primary = {
    args: { label: 'Проголосувати', disabled: false, variant: 'primary' },
    render: Template,
  };
  
  export const Voted = {
    args: { label: 'Голос враховано', disabled: true, variant: 'success' },
    render: Template,
  };