import os
import sys

# Répertoire des drapeaux
flags_dir = "/Users/arnaudkossea/development/kumacodex/assets/flags"

# Liste des drapeaux non-africains à supprimer
non_african_flags = [
    "ad.png", "ae.png", "af.png", "ag.png", "ai.png", "al.png", "am.png", "aq.png", "ar.png", "as.png",
    "at.png", "au.png", "aw.png", "ax.png", "az.png", "ba.png", "bb.png", "bd.png", "be.png", "bg.png",
    "bh.png", "bl.png", "bm.png", "bn.png", "bo.png", "bq.png", "br.png", "bs.png", "bt.png", "bv.png",
    "by.png", "bz.png", "ca.png", "cc.png", "ch.png", "ck.png", "cl.png", "cn.png", "co.png", "cr.png",
    "cu.png", "cw.png", "cx.png", "cy.png", "cz.png", "de.png", "dk.png", "dm.png", "do.png", "ec.png",
    "ee.png", "eh.png", "es.png", "fi.png", "fj.png", "fk.png", "fm.png", "fo.png", "fr.png", "gb-eng.png",
    "gb-nir.png", "gb-sct.png", "gb-wls.png", "gb.png", "gd.png", "ge.png", "gf.png", "gg.png", "gi.png",
    "gl.png", "gp.png", "gr.png", "gs.png", "gt.png", "gu.png", "gy.png", "hk.png", "hm.png", "hn.png",
    "hr.png", "ht.png", "hu.png", "id.png", "ie.png", "il.png", "im.png", "in.png", "io.png", "iq.png",
    "ir.png", "is.png", "it.png", "je.png", "jm.png", "jo.png", "jp.png", "kg.png", "kh.png", "ki.png",
    "kn.png", "kp.png", "kr.png", "kw.png", "ky.png", "kz.png", "la.png", "lb.png", "lc.png", "li.png",
    "lk.png", "lt.png", "lu.png", "lv.png", "mc.png", "md.png", "me.png", "mf.png", "mh.png", "mk.png",
    "mm.png", "mn.png", "mo.png", "mp.png", "mq.png", "ms.png", "mt.png", "mv.png", "mx.png", "my.png",
    "nc.png", "nf.png", "ni.png", "nl.png", "no.png", "np.png", "nr.png", "nu.png", "nz.png", "om.png",
    "pa.png", "pe.png", "pf.png", "pg.png", "ph.png", "pk.png", "pl.png", "pm.png", "pn.png", "pr.png",
    "ps.png", "pt.png", "pw.png", "py.png", "qa.png", "re.png", "ro.png", "rs.png", "ru.png", "sa.png",
    "sb.png", "se.png", "sg.png", "sh.png", "si.png", "sj.png", "sk.png", "sm.png", "sr.png", "sv.png",
    "sx.png", "sy.png", "tc.png", "tf.png", "th.png", "tj.png", "tk.png", "tl.png", "tm.png", "to.png",
    "tr.png", "tt.png", "tv.png", "tw.png", "ua.png", "um.png", "us.png", "uy.png", "uz.png", "va.png",
    "vc.png", "ve.png", "vg.png", "vi.png", "vn.png", "vu.png", "wf.png", "ws.png", "xk.png", "ye.png",
    "yt.png"
]

# Supprimer les fichiers
deleted_count = 0
for file in non_african_flags:
    file_path = os.path.join(flags_dir, file)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            print(f"✅ Deleted: {file}")
            deleted_count += 1
        except Exception as e:
            print(f"❌ Error deleting {file}: {e}")
    else:
        print(f"⚠️  File not found: {file}")

print(f"\n🎉 Deleted {deleted_count} non-African flags")

# Vérifier les fichiers restants
remaining_files = [f for f in os.listdir(flags_dir) if f.endswith('.png')]
print(f"📊 Files remaining: {len(remaining_files)}")

# Lister les fichiers restants
print("\n📋 Remaining flags:")
for file in sorted(remaining_files):
    print(f"  - {file}")

# Exécuter le script
if __name__ == "__main__":
    exec(open(__file__).read())