import { createVoteButton } from './VoteButton.js';

export default {
  title: 'Components/VoteButton',
  tags: ['autodocs'],
  argTypes: {
    label: { control: 'text' },
    disabled: { control: 'boolean' },
    variant: { 
      control: { type: 'select' }, 
      options: ['primary', 'success', 'secondary', 'danger'] 
    },
  },
};

export const Primary = {
  args: { label: 'Проголосувати', disabled: false, variant: 'primary' },
  render: (args) => createVoteButton(args),
};

export const Voted = {
  args: { label: 'Голос враховано', disabled: true, variant: 'success' },
  render: (args) => createVoteButton(args),
};
