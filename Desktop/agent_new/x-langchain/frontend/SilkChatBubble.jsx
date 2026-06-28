import React from 'react';

// type: user 用户 / ai AI回复，入参结构沿用现有msg对象，只改UI渲染
const SilkChatBubble = ({ type, content }) => {
  const isUser = type === 'user';
  return (
    <div className={`flex w-full my-md ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <div className="w-8 h-8 rounded-lg bg-silk-primary/10 flex-shrink-0 mr-sm flex items-center justify-center text-silk-primary">
          A
        </div>
      )}
      <div
        className={`max-w-[65%] px-md py-sm rounded-lg ${
          isUser
            ? 'bg-silk-primary text-white rounded-tr-none'
            : 'bg-silk-neutral-100 text-silk-neutral-800 rounded-tl-none'
        }`}
      >
        <p className="text-sm whitespace-pre-wrap">{content}</p>
      </div>
      {isUser && (
        <div className="w-8 h-8 rounded-full bg-silk-neutral-200 flex-shrink-0 ml-sm flex items-center justify-center text-silk-neutral-600">
          Z
        </div>
      )}
    </div>
  );
};

export default SilkChatBubble;
