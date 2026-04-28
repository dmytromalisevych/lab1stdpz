export const createVoteButton = ({ label, disabled, variant }) => {
    const btn = document.createElement('button');
    btn.className = `btn btn-${variant} w-100`; 
    btn.innerText = label;
    
    if (disabled) {
      btn.disabled = true;
    }
    
    return btn;
  };
