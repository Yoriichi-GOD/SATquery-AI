"""Experimental supervised paired RGB question answering; no masks or ground truth at inference."""
import re
import torch
from torch import nn

def tokens(text):return re.findall(r'[a-z]+|\d+',text.lower())

def encode_questions(questions,vocab,length=32):
    return torch.tensor([[vocab.get(t,1) for t in tokens(q)[:length]]+[0]*max(0,length-len(tokens(q))) for q in questions],dtype=torch.long)

class PairedAnswerModel(nn.Module):
    def __init__(self,vocab_size,answers,question_only=False):
        super().__init__();self.question_only=question_only
        self.embedding=nn.Embedding(vocab_size,96,padding_idx=0)
        self.question=nn.GRU(96,128,batch_first=True,bidirectional=True)
        self.qnorm=nn.LayerNorm(256)
        self.norm=nn.LayerNorm(2048)
        self.visual=nn.Sequential(nn.Linear(8192,256),nn.GELU(),nn.Dropout(.15))
        self.attention=nn.Sequential(nn.Linear(512,128),nn.Tanh(),nn.Linear(128,1))
        self.head=nn.Sequential(nn.Linear(768,384),nn.GELU(),nn.Dropout(.25),nn.Linear(384,answers))
    def forward(self,a,b,q):
        seq,_=self.question(self.embedding(q));mask=(q!=0).unsqueeze(-1)
        text=self.qnorm((seq*mask).sum(1)/mask.sum(1).clamp_min(1))
        if self.question_only:
            visual=torch.zeros_like(text)
        else:
            a=self.norm(a.float());b=self.norm(b.float())
            pixels=self.visual(torch.cat([a,b,b-a,(b-a).abs()],-1))
            attention=self.attention(torch.cat([pixels,text[:,None,:].expand(-1,pixels.shape[1],-1)],-1)).softmax(1)
            visual=(pixels*attention).sum(1)
        return self.head(torch.cat([text,visual,text*visual],-1))
