
def remove_comments(program_code, comment_sym='//'):
    lines = program_code.split('\n')
    out_lines = []
    for line in lines:
        comment_start = line.find(comment_sym)
        if comment_start >= 0:
            line = line[:comment_start]

        out_lines.append(line)

    return '\n'.join(out_lines)
