import torch
import pytorch_lightning as pl
from transformers import AutoModelForCausalLM, AutoTokenizer, AdamW, AutoConfig

class PoetFormer(pl.LightningModule):
    def __init__(self, pretrained_name=None):
        super().__init__()
        self.pretrained_name = pretrained_name
        conf = AutoConfig.from_pretrained(pretrained_name)
        self.model = AutoModelForCausalLM.from_config(conf)
        self.tokenizer = AutoTokenizer.from_pretrained(pretrained_name)
        
            
    def load_pretrained(self):
        self.model = AutoModelForCausalLM.from_pretrained(self.pretrained_name)
        
    def forward(self, inputs):
        res = self.model(**inputs, labels=inputs['input_ids'])
        return res.logits, res.loss

    def step(self, batch, mode='train'):
        outputs, loss = self.forward(batch)
        self.log(mode+'_loss', loss.item())
        return loss

    def training_step(self, batch, batch_idx):
        return self.step(batch)
    
    def validation_step(self, batch, batch_idx):
        self.step(batch, mode='val')
    
    def test_step(self, batch, batch_idx):
        outputs, _ = self.forward(batch)
        return outputs

    def configure_optimizers(self):
        opt = AdamW(self.parameters(), lr=1e-4)
        sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=10, eta_min=1e-8)
        return [opt], [sch]

    def count_parameters(self):
        return sum(p.numel() for p in self.parameters() if p.requires_grad)
    
    def generate(self, prompt='', 
                 poet='حافظ', 
                 max_length=128, 
                 num_return_sequences=1, 
                 topk=100, 
                 top_p=0.9, 
                 n_beam=1, 
                 no_repeat_ngram=4,
                 temperature=0.8):
        
#         print(f'generating poem in "{poet}" style.')
        prompt = f"<s>{poet}<|startoftext|>" + prompt
        generated = torch.tensor(self.tokenizer.encode(prompt)).unsqueeze(0)

        decoded_outputs = self.model.generate(
            generated,
            do_sample=True,
            top_k=topk,
            max_length=max_length, 
            top_p=top_p,
            num_beams=n_beam,
            temperature=temperature,
            no_repeat_ngram_size=no_repeat_ngram,
            num_return_sequences=num_return_sequences
        )
        
        outputs = []
        for i, output in enumerate(decoded_outputs):
            o = self.tokenizer.decode(output, skip_special_tokens=False)
            o = o.replace("<s>", "").replace("</s>", "").replace('<|startoftext|>', ':\n').replace('<sep>', '\n')
            outputs += [o]
        return outputs
            
