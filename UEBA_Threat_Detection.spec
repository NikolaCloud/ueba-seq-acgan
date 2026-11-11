# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\UserB519\\Desktop\\UEBA_Codex\\src\\ueba_seq_acgan\\__main__.py'],
    pathex=['C:\\Users\\UserB519\\Desktop\\UEBA_Codex\\src'],
    binaries=[('D:\\Program\\Lib\\site-packages\\xgboost\\lib\\xgboost.dll', 'xgboost/lib')],
    datas=[('C:\\Users\\UserB519\\Desktop\\UEBA_Codex\\src\\ueba_seq_acgan\\web', 'src/ueba_seq_acgan/web'), ('C:\\Users\\UserB519\\Desktop\\UEBA_Codex\\configs', 'configs'), ('C:\\Users\\UserB519\\Desktop\\UEBA_Codex\\artifacts\\dashboard', 'artifacts/dashboard'), ('C:\\Users\\UserB519\\Desktop\\UEBA_Codex\\artifacts\\r5.2_normal_role_conditional_gan', 'artifacts/r5.2_normal_role_conditional_gan'), ('C:\\Users\\UserB519\\Desktop\\UEBA_Codex\\artifacts\\r5.2_mitre_augmented_seq_acgan', 'artifacts/r5.2_mitre_augmented_seq_acgan'), ('C:\\Users\\UserB519\\Desktop\\UEBA_Codex\\artifacts\\r5.2_gpu_detector', 'artifacts/r5.2_gpu_detector'), ('C:\\Users\\UserB519\\Desktop\\UEBA_Codex\\artifacts\\r5.2_low_shot_gan', 'artifacts/r5.2_low_shot_gan'), ('C:\\Users\\UserB519\\Desktop\\UEBA_Codex\\data\\processed\\r5.2_sequences\\validation.npz', 'data/processed/r5.2_sequences'), ('C:\\Users\\UserB519\\Desktop\\UEBA_Codex\\data\\processed\\r5.2_sequences\\manifest.json', 'data/processed/r5.2_sequences'), ('C:\\Users\\UserB519\\Desktop\\UEBA_Codex\\data\\raw\\cert\\r5.2\\r5.2\\LDAP', 'data/raw/cert/r5.2/r5.2/LDAP'), ('D:\\Program\\Lib\\site-packages\\xgboost', 'xgboost')],
    hiddenimports=['torch', 'torch.nn', 'torch.nn.functional', 'xgboost', 'xgboost.core', 'xgboost.training', 'xgboost.sklearn', 'sklearn', 'sklearn.ensemble', 'sklearn.preprocessing', 'sklearn.preprocessing._data', 'sklearn.utils', 'joblib', 'joblib.numpy_pickle', 'numpy', 'scipy', 'scipy.stats', 'scipy.signal', 'scipy.sparse', 'pandas', 'ueba_seq_acgan', 'ueba_seq_acgan.transforms', 'ueba_seq_acgan.models', 'ueba_seq_acgan.synthetic', 'ueba_seq_acgan.risk', 'ueba_seq_acgan.ldap', 'ueba_seq_acgan.identity', 'ueba_seq_acgan.paths', 'ueba_seq_acgan.dashboard', 'ueba_seq_acgan.audit', 'ueba_seq_acgan.trust'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='UEBA_Threat_Detection',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['C:\\Users\\UserB519\\Desktop\\UEBA_Codex\\icon.ico'],
)
