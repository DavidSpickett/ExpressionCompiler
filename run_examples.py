import os
import subprocess
import sys

examples = os.listdir("examples")
examples = [f for f in examples if not f.endswith(".expected")]
# Ignore vim temp files
examples = [f for f in examples if not f.startswith(".")]
examples = [os.path.splitext(f)[0] for f in examples]
exit_code = 0

for f in examples:
    print("Running {}.ls ... ".format(f), end='')

    args = ["python3", "main.py",
            os.path.join("examples", f+".ls")]
    got = subprocess.check_output(args, universal_newlines=True)

    tmp_path = os.path.join("/tmp", f+".out")
    with open(tmp_path, 'w+') as outfile:
        outfile.write(got)

    check_args = ["diff", os.path.join("examples", f+".expected"),
                  tmp_path]
    check = subprocess.run(check_args)

    if not check.returncode:
        print("passed.")
    else:
        exit_code = 1
        print("failed.")

sys.exit(exit_code)
