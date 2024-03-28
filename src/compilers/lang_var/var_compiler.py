from lang_var.var_ast import *
from common.wasm import *
import lang_var.var_tychecker as var_tychecker
from common.compilerSupport import *
# import common.utils as utils


def compileModule(m: mod, cfg: CompilerConfig) -> WasmModule:
    vars = var_tychecker.tycheckModule(m)
    instrs = compileStmts(m.stmts)
    idMain = WasmId('$main')
    locals: list[tuple[WasmId, WasmValtype]] = [(identToWasmId(x), 'i64') for x in vars]
    return WasmModule(imports=wasmImports(cfg.maxMemSize),
                      exports=[WasmExport("main", WasmExportFunc(idMain))],
                      globals=[],
                      data=[],
                      funcTable=WasmFuncTable([]),
                      funcs=[WasmFunc(idMain, [], None, locals, instrs)])   

def compileStmts(stmts: list[stmt]) -> list[WasmInstr]:
    wasm_instrs: list[WasmInstr] = []
    for stmt in stmts:
        wasm_instrs.extend(compileStmt(stmt))
    return wasm_instrs

def compileStmt(stmt: stmt) -> list[WasmInstr]:
    match stmt:
        case StmtExp():
            return compileExp(stmt.exp)
        case Assign(var, right):
            return compileAssign(var, right)
    
def compileExp(exp: exp) -> list[WasmInstr]:
    wasm_instrs: list[WasmInstr] = [] # later the return value

    match exp:
        case IntConst(value):
            wasm_instrs.append(WasmInstrConst('i64', value)) # just return int
        case Call(name):
            wasm_instrs.extend(compileCall(exp)) # call print or input
        case UnOp(USub(), sub): # subtracting 0 - x = -x
                wasm_instrs.append(WasmInstrConst(ty='i64', val=0))
                wasm_instrs.extend(compileExp(sub))
                wasm_instrs.append(WasmInstrNumBinOp(ty='i64', op='sub'))
        case BinOp(left, op, right):
            wasm_instrs+= compileExp(left)
            wasm_instrs+= compileExp(right)
            match op:
                case Sub():
                    wasm_instrs.append(WasmInstrNumBinOp(ty='i64', op='sub'))
                case Add():
                    wasm_instrs.append(WasmInstrNumBinOp(ty='i64', op='add'))
                case Mul():
                    wasm_instrs.append(WasmInstrNumBinOp(ty='i64', op='mul'))
        case Name(name):
            wasm_instrs.append(WasmInstrVarLocal(op='get', id=identToWasmId(name)))
    return wasm_instrs
    
def compileCall(call: Call) -> list[WasmInstr]:
    match call:
        case Call(Ident('print'), args):
            return compilePrint(args)
        case Call(Ident('input_int'), args):
            return [WasmInstrCall(WasmId('$input_i64'))]
        case _:
            raise ValueError("Unsupported function call: ", call)

def compilePrint(args: list[exp]) -> list[WasmInstr]:
    instrs: list[WasmInstr] = []
    for arg in args:
        instrs.extend(compileExp(arg))
    instrs.append(WasmInstrCall(WasmId('$print_i64')))
    return instrs

def compileAssign(var: Ident, right: exp) -> list[WasmInstr]:
    instrs: list[WasmInstr] = compileExp(right)
    instrs.append(WasmInstrVarLocal(op='set', id=identToWasmId(var)))
    return instrs

def identToWasmId(ident: Ident) -> WasmId:
    return WasmId('$' + ident.name)